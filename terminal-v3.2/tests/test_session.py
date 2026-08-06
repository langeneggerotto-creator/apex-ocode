"""Unit tests for the session spawn/stop primitives.

Prerequisite-gated the same way Bite 1's isolation tests are: these need Linux,
root, `unshare`/`setpriv`, and libseccomp. Fail closed, so skip rather than fake a
pass when a primitive is unavailable.
"""

from __future__ import annotations

import os
import platform
import select
import shutil
import time
from pathlib import Path

import pytest

from ocode_sandbox.seccomp_policy import seccomp_available
from ocode_sandbox.trust import establish_trust

from ocode_terminal import session
from ocode_terminal.session import WorkspaceNotTrustedError

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
        "session spawn/stop tests require Linux, root, `unshare`/`setpriv`, and "
        "libseccomp; skipped rather than faked when a primitive is unavailable"
    ),
)


@pytest.fixture()
def trusted_workspace(tmp_path: Path) -> Path:
    establish_trust(tmp_path, actor="test-suite")
    return tmp_path


def _wait_for_marker(master_fd: int, marker: bytes, timeout: float = 5.0) -> None:
    """Block until ``marker`` has appeared in the PTY output. Stop-escalation tests
    need this: sending SIGTERM immediately after spawn() races the target's own
    early initialization (e.g. a `trap` statement it hasn't executed yet) — that's
    a property of the target program's startup, not something spawn()'s own
    readiness handshake covers (spawn() only promises the *sandbox* is ready to
    forward signals, not that the target has finished its own first statements).
    """
    deadline = time.time() + timeout
    buf = b""
    while marker not in buf and time.time() < deadline:
        r, _, _ = select.select([master_fd], [], [], max(0, deadline - time.time()))
        if r:
            buf += os.read(master_fd, 65536)
    assert marker in buf, f"marker {marker!r} did not appear within {timeout}s (got {buf!r})"


def test_untrusted_workspace_refused_before_any_process_spawns(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceNotTrustedError):
        session.spawn(tmp_path, ["true"], run_id="untrusted-1")


def test_spawn_discovers_real_child_pid_and_stop_cleans_up(trusted_workspace: Path) -> None:
    spawned = session.spawn(trusted_workspace, ["bash", "-c", "sleep 5"], run_id="pid-discovery")
    try:
        assert spawned.child_pid > 0
        os.kill(spawned.child_pid, 0)  # raises if the process doesn't really exist
    finally:
        result = session.stop(spawned, grace_seconds=2)
    assert result.exit_code is not None


def test_graceful_stop_honored_when_target_traps_sigterm(trusted_workspace: Path) -> None:
    spawned = session.spawn(
        trusted_workspace,
        ["bash", "-c", "trap 'exit 0' TERM; echo READY; while true; do sleep 0.2; done"],
        run_id="graceful",
    )
    # Wait for the target to have actually registered its trap (evidenced by its
    # own READY echo) before stopping it — sending SIGTERM any earlier races the
    # target's own startup, independent of whether the sandbox forwarded it
    # correctly, which is not what this test is checking.
    _wait_for_marker(spawned.master_fd, b"READY")
    result = session.stop(spawned, grace_seconds=5)
    assert result.escalated is False


def test_forced_escalation_for_process_that_ignores_sigterm(trusted_workspace: Path) -> None:
    # An explicit `trap '' TERM` ignores the signal deterministically once
    # registered — but registration itself still takes a moment (the target has to
    # start and run its own first statement), so this waits for READY the same way
    # the graceful-stop test above does, isolating "does escalation work" from
    # "did the signal arrive before the target set up its trap".
    spawned = session.spawn(
        trusted_workspace,
        ["bash", "-c", "trap '' TERM; echo READY; while true; do sleep 0.2; done"],
        run_id="escalation",
    )
    _wait_for_marker(spawned.master_fd, b"READY")
    result = session.stop(spawned, grace_seconds=1.5)
    assert result.escalated is True
