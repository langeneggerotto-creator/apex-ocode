"""JobManager: an in-process job queue with a bounded worker pool enforcing a
concurrency limit, the queued/leased/running/succeeded/failed/cancelled/timed-out
state machine, cancellation, and evidence capture. Used directly by tests and
wrapped by ``daemon.py`` for the cross-process (Unix socket) surface the CLI uses.
"""

from __future__ import annotations

import collections
import json
import threading
import time
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Sequence

from ocode_sandbox.cgroups import ResourceLimits
from ocode_sandbox.evidence import scrub

from . import executor
from .job import Job, JobState, TERMINAL_STATES, new_job_id

WORKER_POLL_SECONDS = 0.5


class JobManager:
    def __init__(
        self,
        workspace: Path,
        *,
        concurrency: int = 2,
        evidence_dir: Optional[Path] = None,
    ):
        self.workspace = Path(workspace)
        self.concurrency = concurrency
        self.evidence_dir = Path(evidence_dir) if evidence_dir else None

        self._jobs: Dict[str, Job] = {}
        self._limits: Dict[str, Optional[ResourceLimits]] = {}
        self._captured_logs: Dict[str, bytes] = {}
        self._running: Dict[str, executor.RunningJob] = {}
        self._cancel_requested: set = set()
        self._queue: Deque[str] = collections.deque()

        self._lock = threading.Lock()
        self._queue_cv = threading.Condition(self._lock)
        self._shutdown_event = threading.Event()

        self._workers = [
            threading.Thread(target=self._worker_loop, daemon=True, name=f"ocode-task-worker-{i}")
            for i in range(concurrency)
        ]
        for w in self._workers:
            w.start()

    # -- public API ----------------------------------------------------------

    def submit(
        self,
        command: Sequence[str],
        *,
        task_name: Optional[str] = None,
        timeout_seconds: int = 600,
        limits: Optional[ResourceLimits] = None,
    ) -> str:
        job = Job(
            job_id=new_job_id(),
            task_name=task_name,
            command=list(command),
            workspace=str(self.workspace),
            timeout_seconds=timeout_seconds,
        )
        with self._lock:
            self._jobs[job.job_id] = job
            self._limits[job.job_id] = limits
            self._queue.append(job.job_id)
            self._queue_cv.notify()
        return job.job_id

    def status(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> List[Job]:
        with self._lock:
            return list(self._jobs.values())

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.state in TERMINAL_STATES:
                return False
            if job.state == JobState.QUEUED and job_id in self._queue:
                # Still sitting in the queue, untouched by any worker: cancel it
                # synchronously right here rather than just marking intent and
                # waiting for a worker to eventually notice — with all worker
                # slots busy, "eventually" could be an arbitrarily long wait,
                # and a cancelled-but-still-reporting-QUEUED job is a confusing
                # status to show a caller in the meantime.
                self._queue.remove(job_id)
                job.transition(JobState.CANCELLED)
                self._captured_logs[job_id] = b""
                write_evidence = True
            else:
                self._cancel_requested.add(job_id)
                write_evidence = False
            running = self._running.get(job_id)
        if running is not None:
            # Proactively kill now rather than waiting for the worker's wait()
            # call to hit the job's (possibly long) timeout on its own.
            executor.cancel(running)
        if write_evidence:
            self._write_evidence(job)
        return True

    def logs(self, job_id: str) -> Optional[bytes]:
        with self._lock:
            if job_id in self._captured_logs:
                return self._captured_logs[job_id]
            running = self._running.get(job_id)
        if running is not None:
            return running.stdout.snapshot() + running.stderr.snapshot()
        return None

    def shutdown(self, timeout: float = 10.0) -> None:
        self._shutdown_event.set()
        with self._queue_cv:
            self._queue_cv.notify_all()
        for w in self._workers:
            w.join(timeout=timeout)

    # -- worker pool -----------------------------------------------------------

    def _worker_loop(self) -> None:
        while not self._shutdown_event.is_set():
            with self._queue_cv:
                while not self._queue and not self._shutdown_event.is_set():
                    self._queue_cv.wait(timeout=WORKER_POLL_SECONDS)
                if self._shutdown_event.is_set() and not self._queue:
                    return
                if not self._queue:
                    continue
                job_id = self._queue.popleft()
                job = self._jobs[job_id]
                cancelled_before_lease = job_id in self._cancel_requested
                if not cancelled_before_lease:
                    job.transition(JobState.LEASED)

            if cancelled_before_lease:
                with self._lock:
                    job.transition(JobState.CANCELLED)
                    self._cancel_requested.discard(job_id)
                    self._captured_logs[job_id] = b""
                self._write_evidence(job)
                continue

            self._execute(job)

    def _execute(self, job: Job) -> None:
        with self._lock:
            cancelled = job.job_id in self._cancel_requested
        if cancelled:
            with self._lock:
                job.transition(JobState.CANCELLED)
                self._cancel_requested.discard(job.job_id)
                self._captured_logs[job.job_id] = b""
            self._write_evidence(job)
            return

        try:
            running = executor.start(
                self.workspace,
                job.command,
                run_id=job.job_id,
                limits=self._limits.get(job.job_id),
            )
        except (executor.WorkspaceNotTrustedError, executor.SandboxSetupError) as exc:
            with self._lock:
                job.error_message = scrub(str(exc))
                job.transition(JobState.FAILED)
                self._captured_logs[job.job_id] = b""
            self._write_evidence(job)
            return

        with self._lock:
            job.transition(JobState.RUNNING)
            job.controls_applied = running.controls_applied
            self._running[job.job_id] = running

        exit_code = executor.wait(running, timeout=job.timeout_seconds)
        timed_out = exit_code is None
        with self._lock:
            cancelled = job.job_id in self._cancel_requested

        if timed_out or cancelled:
            executor.cancel(running)
            exit_code = running.outer_proc.returncode

        stdout = running.stdout.snapshot()
        stderr = running.stderr.snapshot()
        usage = executor.resource_usage(running)
        executor.cleanup(running)

        with self._lock:
            self._running.pop(job.job_id, None)
            job.exit_code = exit_code
            job.resource_usage = usage
            self._captured_logs[job.job_id] = stdout + stderr
            if cancelled:
                job.transition(JobState.CANCELLED)
                self._cancel_requested.discard(job.job_id)
            elif timed_out:
                job.transition(JobState.TIMED_OUT)
            elif exit_code == 0:
                job.transition(JobState.SUCCEEDED)
            else:
                job.transition(JobState.FAILED)

        self._write_evidence(job, stdout=stdout, stderr=stderr)

    # -- evidence --------------------------------------------------------------

    def _write_evidence(self, job: Job, stdout: bytes = b"", stderr: bytes = b"") -> None:
        if self.evidence_dir is None:
            return
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "schema_version": "ocode.task-job-evidence.v1",
            "job_id": job.job_id,
            "task_name": job.task_name,
            "command": [scrub(part) for part in job.command],
            "workspace": job.workspace,
            "state": job.state.value,
            "submitted_at": job.submitted_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "timeout_seconds": job.timeout_seconds,
            "exit_code": job.exit_code,
            "error_message": job.error_message,
            "controls_applied": job.controls_applied,
            "resource_usage": job.resource_usage,
            "stdout_tail": scrub(stdout[-4096:].decode("utf-8", errors="replace")),
            "stderr_tail": scrub(stderr[-4096:].decode("utf-8", errors="replace")),
        }
        out_path = self.evidence_dir / f"task-job-{job.job_id}.json"
        out_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
