"""Spawn a sandboxed, PTY-attached process and manage its lifecycle.

Reuses Bite 1's (`ocode_sandbox`) trust check, cgroup resource limits, mount/
namespace isolation script, and seccomp-applying exec helper unchanged — this
module adds a PTY and process-lifecycle layer on top, it does not reimplement or
modify any isolation control.
"""

from __future__ import annotations

import dataclasses
import fcntl
import json
import os
import pty
import select
import shlex
import signal
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from ocode_sandbox.cgroups import CgroupSandbox, ResourceLimits
from ocode_sandbox.fs_isolation import build_mount_script
from ocode_sandbox.seccomp_policy import DENIED_SYSCALLS, seccomp_available
from ocode_sandbox.trust import verify_trust

DEFAULT_COLS = 80
DEFAULT_ROWS = 24
CHILD_DISCOVERY_ATTEMPTS = 100
CHILD_DISCOVERY_DELAY_SECONDS = 0.05


class WorkspaceNotTrustedError(RuntimeError):
    """Same fail-closed contract as Bite 1: no valid trust marker, no session."""


class SandboxSetupError(RuntimeError):
    """A mandatory isolation control could not be established; nothing was spawned."""


class ChildDiscoveryError(RuntimeError):
    """The sandboxed process's real (host-visible) PID could not be determined,
    so it cannot be signalled directly for graceful stop escalation."""


@dataclasses.dataclass
class SpawnedSession:
    run_id: str
    master_fd: int
    outer_proc: subprocess.Popen
    child_pid: int
    cgroup: CgroupSandbox
    controls_applied: Dict[str, Any]
    cols: int
    rows: int


def set_winsize(fd: int, cols: int, rows: int) -> None:
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


def _discover_child_pid(outer_pid: int) -> int:
    children_path = Path(f"/proc/{outer_pid}/task/{outer_pid}/children")
    for _ in range(CHILD_DISCOVERY_ATTEMPTS):
        try:
            text = children_path.read_text().strip()
        except OSError:
            text = ""
        if text:
            return int(text.split()[0])
        time.sleep(CHILD_DISCOVERY_DELAY_SECONDS)
    raise ChildDiscoveryError(f"no child of pid {outer_pid} appeared in /proc within timeout")


def _wait_for_ready_sentinel(master_fd: int, *, timeout: float) -> None:
    """Block until ``_pty_init``'s fixed-length readiness sentinel has been read in
    full from the PTY. This is what makes it safe to call ``stop()`` immediately
    after ``spawn()`` returns — see ``_pty_init.py`` for why a signal sent before
    this point can be silently dropped rather than merely delayed. Raises
    ``SandboxSetupError`` on timeout or if the child died before signalling ready,
    rather than returning control to a caller who could race the same window this
    exists to close.
    """
    from ._pty_init import READY_SENTINEL

    deadline = time.time() + timeout
    buf = b""
    while len(buf) < len(READY_SENTINEL):
        remaining = deadline - time.time()
        if remaining <= 0:
            raise SandboxSetupError("timed out waiting for sandboxed process readiness sentinel")
        r, _, _ = select.select([master_fd], [], [], remaining)
        if not r:
            continue
        try:
            chunk = os.read(master_fd, len(READY_SENTINEL) - len(buf))
        except OSError as exc:
            raise SandboxSetupError(f"sandboxed process died before signalling ready: {exc}") from exc
        if not chunk:
            raise SandboxSetupError("sandboxed process closed its PTY before signalling ready")
        buf += chunk
    if buf != READY_SENTINEL:
        raise SandboxSetupError(f"unexpected readiness handshake from sandboxed process: {buf!r}")


def spawn(
    workspace_dir: Path,
    command: Sequence[str],
    *,
    run_id: str,
    protected_paths: Optional[Sequence[Path]] = None,
    limits: Optional[ResourceLimits] = None,
    cols: int = DEFAULT_COLS,
    rows: int = DEFAULT_ROWS,
) -> SpawnedSession:
    workspace_dir = Path(workspace_dir).resolve()

    trust_record = verify_trust(workspace_dir)
    if trust_record is None:
        raise WorkspaceNotTrustedError(
            f"workspace is not trusted (no valid trust marker): {workspace_dir}"
        )

    if not seccomp_available():
        raise SandboxSetupError(
            "seccomp (pyseccomp/libseccomp) unavailable; refusing to start an "
            "unconfined sandboxed terminal"
        )

    limits = limits or ResourceLimits()
    protected = list(protected_paths or [])
    protected.append(workspace_dir / ".ocode")

    # Use ocode_terminal's own init/reaper shim, not ocode_sandbox._exec_helper
    # directly: the target must land on PID 2+ of the new PID namespace (not PID 1)
    # for graceful SIGTERM delivery to work at all. See _pty_init.py for why.
    init_argv = [sys.executable, "-m", "ocode_terminal._pty_init", json.dumps(list(command))]
    setpriv_argv = [
        "setpriv",
        "--inh-caps=-all",
        "--bounding-set=-all",
        "--no-new-privs",
        "--",
        *init_argv,
    ]

    cgroup = CgroupSandbox(limits, name=f"ocode-terminal-{run_id}")
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

        master_fd, slave_fd = pty.openpty()
        set_winsize(slave_fd, cols, rows)

        def _preexec() -> None:
            os.setsid()
            fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)

        proc = subprocess.Popen(
            outer_argv,
            cwd=str(workspace_dir),
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=_preexec,
            close_fds=True,
        )
        os.close(slave_fd)

        try:
            child_pid = _discover_child_pid(proc.pid)
            _wait_for_ready_sentinel(master_fd, timeout=15)
        except (ChildDiscoveryError, SandboxSetupError):
            proc.kill()
            proc.wait(timeout=5)
            os.close(master_fd)
            raise

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
            "pty": True,
        }

        return SpawnedSession(
            run_id=run_id,
            master_fd=master_fd,
            outer_proc=proc,
            child_pid=child_pid,
            cgroup=cgroup,
            controls_applied=controls_applied,
            cols=cols,
            rows=rows,
        )
    except Exception:
        cgroup.__exit__(None, None, None)
        raise


@dataclasses.dataclass
class StopResult:
    escalated: bool
    exit_code: Optional[int]


def signal_stop(
    spawned: SpawnedSession,
    *,
    grace_seconds: float = 5.0,
    force: bool = False,
    on_escalate: Optional[Callable[[], None]] = None,
) -> bool:
    """Graceful-then-forced stop escalation: SIGTERM the sandboxed process's real
    PID directly, poll (non-blocking) for up to grace_seconds, SIGKILL if it hasn't
    exited (many real interactive programs, e.g. an interactive bash shell, ignore
    SIGTERM entirely by design — SIGKILL is the only signal guaranteed to work,
    which is exactly why this escalation path exists). ``force`` skips straight to
    SIGKILL. Returns whether escalation to SIGKILL happened.

    ``on_escalate``, if given, fires synchronously at the moment SIGKILL is about to
    be sent — i.e. strictly before the target process can possibly have died from
    it. A caller (the daemon) that has a separate thread racing to detect the
    process's actual death via PTY EOF needs to know "was this escalated" from a
    point that's causally before that detection can fire, not from this function's
    return value (which only arrives after polling *confirms* death, by which point
    the reader thread's independent EOF-triggered broadcast may have already fired
    using a stale, not-yet-updated flag).

    Deliberately signal-only: it does not call ``outer_proc.wait()`` with a blocking
    timeout, does not reap, and does not touch the cgroup. A caller that also owns a
    background thread reading the process's output (the daemon's reader loop) needs
    to be the *sole* place that reaps and cleans up — two threads independently
    calling a blocking ``wait()``/close on the same process race on which one
    observes and reports the true outcome. Standalone callers with no such reader
    thread should use ``stop()`` instead, which adds reap + cleanup on top of this.
    """
    if force:
        if on_escalate is not None:
            on_escalate()
        _safe_kill(spawned.child_pid, signal.SIGKILL)
        _poll_until_exited(spawned.outer_proc, timeout=grace_seconds)
        return True

    _safe_kill(spawned.child_pid, signal.SIGTERM)
    if _poll_until_exited(spawned.outer_proc, timeout=grace_seconds):
        return False

    if on_escalate is not None:
        on_escalate()
    _safe_kill(spawned.child_pid, signal.SIGKILL)
    _poll_until_exited(spawned.outer_proc, timeout=10)
    return True


def _poll_until_exited(proc: subprocess.Popen, *, timeout: float, interval: float = 0.05) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return True
        time.sleep(interval)
    return proc.poll() is not None


def stop(spawned: SpawnedSession, *, grace_seconds: float = 5.0, force: bool = False) -> StopResult:
    """Signal-stop, then reap and clean up. For standalone (non-daemon) callers only
    — see ``signal_stop`` for why the daemon uses that directly instead."""
    try:
        escalated = signal_stop(spawned, grace_seconds=grace_seconds, force=force)
        try:
            spawned.outer_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            # Safety net: kill the outer wrapper too; --kill-child=SIGKILL then
            # tears down any remaining descendant via PID-namespace semantics.
            spawned.outer_proc.kill()
            spawned.outer_proc.wait(timeout=10)
    finally:
        try:
            os.close(spawned.master_fd)
        except OSError:
            pass
        spawned.cgroup.__exit__(None, None, None)

    return StopResult(escalated=escalated, exit_code=spawned.outer_proc.returncode)


def _safe_kill(pid: int, sig: int) -> None:
    try:
        os.kill(pid, sig)
    except ProcessLookupError:
        pass
