"""Job state-machine unit tests (no sandbox prerequisites) plus a basic executor
smoke test (requires the sandbox prerequisites, like Bites 1 and 2's isolation
tests)."""

from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path

import pytest

from ocode_sandbox.seccomp_policy import seccomp_available
from ocode_sandbox.trust import establish_trust

from ocode_tasks import executor
from ocode_tasks.job import InvalidTransitionError, Job, JobState

SANDBOX_PREREQS_MET = (
    platform.system() == "Linux"
    and os.geteuid() == 0
    and shutil.which("unshare") is not None
    and shutil.which("setpriv") is not None
    and seccomp_available()
)


def _make_job() -> Job:
    return Job(job_id="t1", task_name=None, command=["true"], workspace="/tmp", timeout_seconds=10)


def test_valid_transition_sequence() -> None:
    job = _make_job()
    job.transition(JobState.LEASED)
    job.transition(JobState.RUNNING)
    assert job.started_at is not None
    job.transition(JobState.SUCCEEDED)
    assert job.finished_at is not None


def test_leased_can_fail_directly_without_running() -> None:
    # A job whose sandboxed process never actually started (e.g. a fail-closed
    # trust/seccomp check) never reaches RUNNING at all.
    job = _make_job()
    job.transition(JobState.LEASED)
    job.transition(JobState.FAILED)
    assert job.state == JobState.FAILED


def test_invalid_transition_rejected() -> None:
    job = _make_job()
    with pytest.raises(InvalidTransitionError):
        job.transition(JobState.RUNNING)  # cannot skip LEASED


def test_terminal_state_has_no_further_transitions() -> None:
    job = _make_job()
    job.transition(JobState.LEASED)
    job.transition(JobState.CANCELLED)
    with pytest.raises(InvalidTransitionError):
        job.transition(JobState.RUNNING)


@pytest.mark.skipif(
    not SANDBOX_PREREQS_MET,
    reason="executor tests require Linux, root, `unshare`/`setpriv`, and libseccomp",
)
def test_executor_start_wait_cleanup(tmp_path: Path) -> None:
    establish_trust(tmp_path, actor="test-suite")
    running = executor.start(tmp_path, ["bash", "-c", "echo OK"], run_id="exec-smoke")
    exit_code = executor.wait(running, timeout=10)
    assert exit_code == 0
    assert b"OK" in running.stdout.snapshot()
    executor.cleanup(running)


@pytest.mark.skipif(
    not SANDBOX_PREREQS_MET,
    reason="executor tests require Linux, root, `unshare`/`setpriv`, and libseccomp",
)
def test_executor_untrusted_workspace_refused(tmp_path: Path) -> None:
    with pytest.raises(executor.WorkspaceNotTrustedError):
        executor.start(tmp_path, ["true"], run_id="exec-untrusted")
