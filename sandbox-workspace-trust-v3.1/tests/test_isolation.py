"""Adversarial isolation tests + one positive functional test.

Each test proves exactly one claimed control by trying to defeat it and checking that
the attempt failed the expected way. If a prerequisite this bite explicitly requires
(root, Linux namespaces, a writable cgroup controller, libseccomp) is missing on the
host running the suite, the affected tests are skipped with an explicit reason —
never silently treated as passing.
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path

import pytest

from ocode_sandbox.cgroups import CgroupSandbox, ResourceLimits
from ocode_sandbox.runner import WorkspaceNotTrustedError, run_sandboxed
from ocode_sandbox.seccomp_policy import seccomp_available
from ocode_sandbox.trust import establish_trust

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
        "sandbox isolation tests require Linux, root, `unshare`/`setpriv`, and "
        "libseccomp; this bite fails closed rather than run unconfined, so these "
        "tests are skipped rather than faked when a primitive is unavailable"
    ),
)


@pytest.fixture()
def trusted_workspace(tmp_path: Path) -> Path:
    establish_trust(tmp_path, actor="test-suite")
    return tmp_path


def test_untrusted_workspace_is_refused(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceNotTrustedError):
        run_sandboxed(tmp_path, ["true"], timeout_seconds=5)


def test_functional_positive_path(trusted_workspace: Path) -> None:
    result = run_sandboxed(
        trusted_workspace,
        ["bash", "-c", f"echo hello > {trusted_workspace}/proof.txt && cat {trusted_workspace}/proof.txt"],
        timeout_seconds=10,
    )
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert (trusted_workspace / "proof.txt").read_text().strip() == "hello"


def test_network_egress_denied_by_default(trusted_workspace: Path) -> None:
    result = run_sandboxed(
        trusted_workspace,
        ["bash", "-c", "timeout 3 curl -s -o /dev/null -w '%{http_code}' https://example.com; echo x$?"],
        timeout_seconds=10,
    )
    # curl exit code 7 = "failed to connect" (no route in the empty net namespace).
    assert "x7" in result.stdout


def test_filesystem_write_outside_workspace_denied(trusted_workspace: Path) -> None:
    result = run_sandboxed(
        trusted_workspace,
        ["bash", "-c", "touch /etc/ocode-adversarial-write-test"],
        timeout_seconds=10,
    )
    assert result.exit_code != 0
    assert "Read-only file system" in result.stderr


def test_protected_metadata_hidden(trusted_workspace: Path) -> None:
    result = run_sandboxed(
        trusted_workspace,
        ["cat", str(trusted_workspace / ".ocode" / "trust.json")],
        timeout_seconds=10,
    )
    assert result.exit_code != 0
    assert "Permission denied" in result.stderr or "No such file" in result.stderr


def test_memory_limit_enforced(trusted_workspace: Path) -> None:
    result = run_sandboxed(
        trusted_workspace,
        [
            sys.executable,
            "-c",
            "x = bytearray(600 * 1024 * 1024)\n"
            "[x.__setitem__(i, 1) for i in range(0, len(x), 4096)]\n"
            "print('SHOULD_NOT_PRINT')",
        ],
        limits=ResourceLimits(memory_bytes=64 * 1024 * 1024, pids_max=64),
        timeout_seconds=10,
    )
    assert "SHOULD_NOT_PRINT" not in result.stdout
    assert result.exit_code != 0


def test_pid_limit_enforced(trusted_workspace: Path) -> None:
    result = run_sandboxed(
        trusted_workspace,
        ["bash", "-c", "for i in $(seq 1 200); do sleep 5 & done; wait"],
        limits=ResourceLimits(memory_bytes=256 * 1024 * 1024, pids_max=8),
        timeout_seconds=10,
    )
    assert "Resource temporarily unavailable" in result.stderr


def test_privilege_escalation_blocked(trusted_workspace: Path) -> None:
    result = run_sandboxed(
        trusted_workspace,
        [
            "bash",
            "-c",
            "mount -t tmpfs tmpfs /mnt 2>&1; unshare --net -- true 2>&1",
        ],
        timeout_seconds=10,
    )
    assert "permission denied" in result.stdout.lower() or "not permitted" in result.stdout.lower()
    assert "operation not permitted" in result.stdout.lower()


def test_cgroup_unavailable_fails_closed(monkeypatch: pytest.MonkeyPatch, trusted_workspace: Path) -> None:
    def _raise_enter(self):  # noqa: ANN001
        from ocode_sandbox.cgroups import CgroupUnavailableError

        raise CgroupUnavailableError("simulated: no writable controller")

    monkeypatch.setattr(CgroupSandbox, "__enter__", _raise_enter)

    from ocode_sandbox.cgroups import CgroupUnavailableError

    with pytest.raises(CgroupUnavailableError):
        run_sandboxed(trusted_workspace, ["true"], timeout_seconds=5)
