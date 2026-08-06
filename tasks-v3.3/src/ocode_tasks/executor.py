"""Non-blocking sandboxed job execution, reusing Bite 1's isolation primitives
exactly as its own ``runner.py`` does (trust check, mount/namespace isolation
script, cgroup resource limits, seccomp-applying exec helper) — this module adds
no new isolation control and does not modify anything in ``ocode_sandbox``.

Unlike Bite 1's ``run_sandboxed`` (which blocks until completion via
``communicate()``), ``start()`` here returns immediately with a handle a caller can
poll, stream output from, or cancel — needed for a job manager that runs multiple
jobs concurrently and must be able to cancel one mid-flight.
"""

from __future__ import annotations

import dataclasses
import json
import shlex
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ocode_sandbox.cgroups import CgroupSandbox, ResourceLimits
from ocode_sandbox.fs_isolation import build_mount_script
from ocode_sandbox.seccomp_policy import DENIED_SYSCALLS, seccomp_available
from ocode_sandbox.trust import verify_trust


class WorkspaceNotTrustedError(RuntimeError):
    """Same fail-closed contract as Bite 1: no valid trust marker, no job."""


class SandboxSetupError(RuntimeError):
    """A mandatory isolation control could not be established; nothing was spawned."""


class _StreamCapture:
    """Thread-safe append-only byte buffer fed by a background reader thread, with
    a cap so a runaway job's output can't grow evidence/log retrieval unboundedly.
    """

    CAP_BYTES = 4 * 1024 * 1024

    def __init__(self, pipe):
        self._buf = bytearray()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._read_loop, args=(pipe,), daemon=True)
        self._thread.start()

    def _read_loop(self, pipe) -> None:
        try:
            while True:
                chunk = pipe.read(65536)
                if not chunk:
                    break
                with self._lock:
                    self._buf.extend(chunk)
                    overflow = len(self._buf) - self.CAP_BYTES
                    if overflow > 0:
                        del self._buf[:overflow]
        finally:
            try:
                pipe.close()
            except OSError:
                pass

    def snapshot(self) -> bytes:
        with self._lock:
            return bytes(self._buf)

    def join(self, timeout: Optional[float] = None) -> None:
        self._thread.join(timeout=timeout)


@dataclasses.dataclass
class RunningJob:
    outer_proc: subprocess.Popen
    cgroup: CgroupSandbox
    controls_applied: Dict[str, Any]
    stdout: _StreamCapture
    stderr: _StreamCapture


def start(
    workspace_dir: Path,
    command: Sequence[str],
    *,
    run_id: str,
    protected_paths: Optional[Sequence[Path]] = None,
    limits: Optional[ResourceLimits] = None,
) -> RunningJob:
    workspace_dir = Path(workspace_dir).resolve()

    trust_record = verify_trust(workspace_dir)
    if trust_record is None:
        raise WorkspaceNotTrustedError(f"workspace is not trusted (no valid trust marker): {workspace_dir}")

    if not seccomp_available():
        raise SandboxSetupError(
            "seccomp (pyseccomp/libseccomp) unavailable; refusing to start an unconfined job"
        )

    limits = limits or ResourceLimits()
    protected = list(protected_paths or [])
    protected.append(workspace_dir / ".ocode")

    exec_helper_argv = [sys.executable, "-m", "ocode_sandbox._exec_helper", json.dumps(list(command))]
    setpriv_argv = [
        "setpriv",
        "--inh-caps=-all",
        "--bounding-set=-all",
        "--no-new-privs",
        "--",
        *exec_helper_argv,
    ]

    cgroup = CgroupSandbox(limits, name=f"ocode-task-{run_id}")
    cgroup.__enter__()

    try:
        mount_script = build_mount_script(workspace_dir, protected, cgroup.procs_paths())
        inner_script = mount_script + "exec " + " ".join(shlex.quote(part) for part in setpriv_argv) + "\n"
        outer_argv = [
            "unshare",
            "--mount",
            "--uts",
            "--ipc",
            "--pid",
            "--net",
            "--fork",
            "--mount-proc",
            "--kill-child=SIGKILL",
            "--",
            "bash",
            "-c",
            inner_script,
        ]

        proc = subprocess.Popen(
            outer_argv,
            cwd=str(workspace_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        controls_applied: Dict[str, Any] = {
            "workspace_trust": {
                "actor": trust_record.actor,
                "established_at": trust_record.established_at,
            },
            "namespaces": ["mount", "uts", "ipc", "pid", "net"],
            "network_deny_by_default": True,
            "filesystem": {
                "workspace_writable": str(workspace_dir),
                "root_read_only": True,
                "protected_paths_hidden": [str(p) for p in protected],
            },
            "capabilities_dropped": "bounding-set=-all, inheritable=-all, no_new_privs",
            "seccomp_denied_syscalls": list(DENIED_SYSCALLS),
            "cgroup_mode": cgroup.mode,
            "resource_limits": dataclasses.asdict(limits),
        }

        return RunningJob(
            outer_proc=proc,
            cgroup=cgroup,
            controls_applied=controls_applied,
            stdout=_StreamCapture(proc.stdout),
            stderr=_StreamCapture(proc.stderr),
        )
    except Exception:
        cgroup.__exit__(None, None, None)
        raise


def wait(running: RunningJob, *, timeout: Optional[float] = None) -> Optional[int]:
    """Blocking wait for completion, bounded by ``timeout``. Returns the exit code,
    or None if the job is still running when the timeout expires (the caller
    decides what to do — for the manager, that means treating it as a timeout and
    calling cancel())."""
    try:
        running.outer_proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    return running.outer_proc.returncode


def cancel(running: RunningJob) -> None:
    """Single hard kill of the outer sandbox wrapper. ``--kill-child=SIGKILL``
    (Bite 1) cascades to tear down the whole process-namespace subtree. No
    graceful SIGTERM-first here — see PLAN.md for why that's a deliberate scope
    decision for batch/build/test jobs, not an oversight."""
    running.outer_proc.kill()
    try:
        running.outer_proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def cleanup(running: RunningJob) -> None:
    running.stdout.join(timeout=5)
    running.stderr.join(timeout=5)
    try:
        running.cgroup.__exit__(None, None, None)
    except Exception:
        pass


def resource_usage(running: RunningJob) -> Dict[str, Any]:
    return running.cgroup.usage()
