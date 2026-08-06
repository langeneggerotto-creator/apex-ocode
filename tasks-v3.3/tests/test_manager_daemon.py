"""Adversarial + functional tests for JobManager (in-process, fast) and the
JobDaemon/JobClient socket layer (a subset, mirroring Bite 2's split)."""

from __future__ import annotations

import os
import platform
import shutil
import threading
import time
from pathlib import Path

import pytest

from ocode_sandbox.seccomp_policy import seccomp_available
from ocode_sandbox.trust import establish_trust

from ocode_tasks.client import JobClient
from ocode_tasks.daemon import JobDaemon
from ocode_tasks.job import JobState
from ocode_tasks.manager import JobManager

SANDBOX_PREREQS_MET = (
    platform.system() == "Linux"
    and os.geteuid() == 0
    and shutil.which("unshare") is not None
    and shutil.which("setpriv") is not None
    and seccomp_available()
)

pytestmark = pytest.mark.skipif(
    not SANDBOX_PREREQS_MET,
    reason=(
        "job manager/daemon tests require Linux, root, `unshare`/`setpriv`, and "
        "libseccomp; skipped rather than faked when a primitive is unavailable"
    ),
)


def _wait_for_state(mgr: JobManager, job_id: str, *states, timeout: float = 10.0) -> JobState:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = mgr.status(job_id).state
        if last in states:
            return last
        time.sleep(0.1)
    raise AssertionError(f"job {job_id} did not reach {states} within {timeout}s (last: {last})")


@pytest.fixture()
def trusted_workspace(tmp_path: Path) -> Path:
    establish_trust(tmp_path, actor="test-suite")
    return tmp_path


@pytest.fixture()
def manager(trusted_workspace: Path):
    mgr = JobManager(trusted_workspace, concurrency=1)
    yield mgr
    mgr.shutdown()


def test_functional_positive_path(manager: JobManager) -> None:
    job_id = manager.submit(["bash", "-c", "echo POSITIVE_PATH_OK"], timeout_seconds=10)
    _wait_for_state(manager, job_id, JobState.SUCCEEDED, JobState.FAILED)
    job = manager.status(job_id)
    assert job.state == JobState.SUCCEEDED
    assert job.exit_code == 0
    assert b"POSITIVE_PATH_OK" in manager.logs(job_id)


def test_concurrency_limit_enforced(manager: JobManager) -> None:
    # concurrency=1: a second submission must stay QUEUED while the first runs.
    j1 = manager.submit(["bash", "-c", "sleep 1.5"], timeout_seconds=10)
    j2 = manager.submit(["bash", "-c", "echo second"], timeout_seconds=10)
    time.sleep(0.3)
    assert manager.status(j1).state == JobState.RUNNING
    assert manager.status(j2).state == JobState.QUEUED
    _wait_for_state(manager, j2, JobState.SUCCEEDED, JobState.FAILED, timeout=15)
    assert manager.status(j2).state == JobState.SUCCEEDED


def test_cancel_queued_job_never_runs(manager: JobManager) -> None:
    blocker = manager.submit(["bash", "-c", "sleep 3"], timeout_seconds=10)
    _wait_for_state(manager, blocker, JobState.RUNNING)
    queued = manager.submit(["bash", "-c", "echo SHOULD_NEVER_RUN"], timeout_seconds=10)
    assert manager.status(queued).state == JobState.QUEUED
    assert manager.cancel(queued) is True
    assert manager.status(queued).state == JobState.CANCELLED
    manager.cancel(blocker)


def test_cancel_running_job(manager: JobManager) -> None:
    job_id = manager.submit(["bash", "-c", "sleep 30"], timeout_seconds=60)
    _wait_for_state(manager, job_id, JobState.RUNNING)
    t0 = time.time()
    assert manager.cancel(job_id) is True
    _wait_for_state(manager, job_id, JobState.CANCELLED, timeout=15)
    assert time.time() - t0 < 15


def test_timeout_transitions_to_timed_out(manager: JobManager) -> None:
    job_id = manager.submit(["bash", "-c", "sleep 30"], timeout_seconds=1)
    state = _wait_for_state(manager, job_id, JobState.TIMED_OUT, timeout=15)
    assert state == JobState.TIMED_OUT


def test_isolation_still_enforced_inside_a_job(manager: JobManager) -> None:
    command = [
        "bash",
        "-c",
        "touch /etc/ocode-task-adversarial-write-test 2>&1; echo TOUCH_RC_$?; "
        "timeout 3 curl -s -o /dev/null -w '%{http_code}' https://example.com; echo CURL_RC_$?",
    ]
    job_id = manager.submit(command, timeout_seconds=10)
    _wait_for_state(manager, job_id, JobState.SUCCEEDED, JobState.FAILED)
    logs = manager.logs(job_id).decode()
    assert "Read-only file system" in logs
    assert "TOUCH_RC_1" in logs
    assert "CURL_RC_7" in logs  # curl: could not connect (empty netns)


def test_untrusted_workspace_refused(tmp_path: Path) -> None:
    mgr = JobManager(tmp_path, concurrency=1)
    try:
        job_id = mgr.submit(["true"], timeout_seconds=5)
        _wait_for_state(mgr, job_id, JobState.FAILED)
        job = mgr.status(job_id)
        assert job.state == JobState.FAILED
        assert "not trusted" in (job.error_message or "")
    finally:
        mgr.shutdown()


def test_logs_are_secret_scrubbed_in_evidence(trusted_workspace: Path) -> None:
    evidence_dir = trusted_workspace / ".ocode" / "evidence"
    mgr = JobManager(trusted_workspace, concurrency=1, evidence_dir=evidence_dir)
    try:
        job_id = mgr.submit(["bash", "-c", "echo api_key=supersecrettoken12345678901234"], timeout_seconds=10)
        _wait_for_state(mgr, job_id, JobState.SUCCEEDED, JobState.FAILED)
    finally:
        mgr.shutdown()
    evidence_path = evidence_dir / f"task-job-{job_id}.json"
    assert evidence_path.is_file()
    text = evidence_path.read_text()
    assert "supersecrettoken12345678901234" not in text
    assert "REDACTED" in text


# -- daemon/client layer (a subset; JobManager tests above cover the bulk of the
# state-machine/isolation/cancellation behavior at the faster, in-process layer) --


def _start_daemon(workspace: Path, socket_name: str, **kwargs):
    socket_path = workspace / ".ocode" / "tasks" / socket_name
    daemon = JobDaemon(workspace, socket_path, **kwargs)
    t = threading.Thread(target=daemon.run, daemon=True)
    t.start()
    for _ in range(100):
        if socket_path.exists():
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("daemon socket never appeared")
    return daemon, t, socket_path


def test_daemon_client_submit_status_logs_list_shutdown(trusted_workspace: Path) -> None:
    daemon, t, sock = _start_daemon(trusted_workspace, "d1.sock", concurrency=2)
    client = JobClient(sock)

    job_id = client.submit(["bash", "-c", "echo DAEMON_CLIENT_OK"], timeout_seconds=10)

    deadline = time.time() + 10
    status = None
    while time.time() < deadline:
        status = client.status(job_id)
        if status["state"] in ("succeeded", "failed"):
            break
        time.sleep(0.1)
    assert status["state"] == "succeeded"
    assert b"DAEMON_CLIENT_OK" in client.logs(job_id)

    jobs = client.list()
    assert any(j["job_id"] == job_id for j in jobs)

    client.shutdown()
    t.join(timeout=10)
    assert not t.is_alive()
    assert not sock.exists()


def test_daemon_reachable_from_separate_client_connections(trusted_workspace: Path) -> None:
    """Distinct connections (simulating separate CLI invocations) see the same
    job state — proving the daemon, not any single connection, owns the truth."""
    daemon, t, sock = _start_daemon(trusted_workspace, "d2.sock", concurrency=1)
    submitter = JobClient(sock)
    job_id = submitter.submit(["bash", "-c", "echo SEEN_FROM_ANOTHER_CONNECTION"], timeout_seconds=10)

    checker = JobClient(sock)
    deadline = time.time() + 10
    status = None
    while time.time() < deadline:
        status = checker.status(job_id)
        if status["state"] in ("succeeded", "failed"):
            break
        time.sleep(0.1)
    assert status["state"] == "succeeded"

    JobClient(sock).shutdown()
    t.join(timeout=10)
