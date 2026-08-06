"""Adversarial + functional tests for the daemon/client protocol.

Most tests host the daemon in a background thread within the test process — the
daemon's own logic (protocol, scrollback, watchdog, isolation reuse) doesn't need a
separate OS process to be exercised for real, and this keeps the suite fast. True
cross-process persistence (the actual "survives the CLI process exiting" claim) is
proven separately in ``test_cli_daemon_survives_launching_process_exit``, which goes
through the real ``python -m ocode_terminal start`` subprocess path.
"""

from __future__ import annotations

import base64
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from ocode_sandbox.seccomp_policy import seccomp_available
from ocode_sandbox.trust import establish_trust

from ocode_terminal.client import SessionUnavailableError, TerminalClient
from ocode_terminal.daemon import SessionDaemon
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
        "daemon/client tests require Linux, root, `unshare`/`setpriv`, and "
        "libseccomp; skipped rather than faked when a primitive is unavailable"
    ),
)


def _start_daemon(workspace: Path, command, run_id: str, **kwargs) -> tuple[SessionDaemon, threading.Thread, Path]:
    establish_trust(workspace, actor="test-suite")
    sock = workspace / ".ocode" / "terminal" / f"{run_id}.sock"
    evidence_dir = workspace / ".ocode" / "evidence"
    daemon = SessionDaemon(workspace, command, sock, run_id=run_id, evidence_dir=evidence_dir, **kwargs)
    t = threading.Thread(target=daemon.run, daemon=True)
    t.start()
    for _ in range(100):
        if sock.exists():
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("daemon socket never appeared within timeout")
    return daemon, t, sock


def _drain_until(client: TerminalClient, predicate, timeout: float = 8.0) -> str:
    collected = ""
    deadline = time.time() + timeout
    while time.time() < deadline:
        msg = client.read_message()
        if msg is None:
            break
        if msg.get("type") == "output":
            collected += base64.b64decode(msg["data"]).decode("utf-8", errors="replace")
            if predicate(collected):
                return collected
    return collected


def test_reconnect_preserves_scrollback_across_separate_clients(tmp_path: Path) -> None:
    daemon, t, sock = _start_daemon(tmp_path, ["bash", "-i"], "reconnect")

    c1 = TerminalClient(sock)
    c1.attach()
    c1.send_input(b"echo RECONNECT_MARKER\n")
    _drain_until(c1, lambda s: "RECONNECT_MARKER" in s, timeout=5)
    c1.detach()

    c2 = TerminalClient(sock)
    scrollback = c2.attach()
    assert b"RECONNECT_MARKER" in scrollback

    c2.stop(force=True)
    t.join(timeout=15)
    assert not t.is_alive()


def test_resize_changes_real_pty_winsize(tmp_path: Path) -> None:
    daemon, t, sock = _start_daemon(tmp_path, ["bash", "-i"], "resize")
    c = TerminalClient(sock)
    c.attach()
    c.resize(100, 40)
    c.send_input(b"stty size\n")
    output = _drain_until(c, lambda s: "40 100" in s, timeout=5)
    assert "40 100" in output

    c.stop(force=True)
    t.join(timeout=15)


def test_idle_timeout_stops_session_automatically(tmp_path: Path) -> None:
    daemon, t, sock = _start_daemon(
        tmp_path, ["bash", "-i"], "idle", idle_timeout_seconds=1.0, grace_seconds=1.0
    )
    c = TerminalClient(sock)
    c.attach()
    c.detach()  # stop interacting; let the idle watchdog fire

    t.join(timeout=15)
    assert not t.is_alive()
    with pytest.raises(SessionUnavailableError):
        TerminalClient(sock)


def test_isolation_still_enforced_inside_a_terminal_session(tmp_path: Path) -> None:
    """Proves Bite 2 didn't bypass Bite 1's controls by routing through a PTY
    instead of pipes: network egress and filesystem-escape are still denied."""
    daemon, t, sock = _start_daemon(tmp_path, ["bash", "-i"], "isolation")
    c = TerminalClient(sock)
    c.attach()
    # Predicates check for the *expanded exit code* (e.g. "TOUCH_RC_1"), which only
    # appears once the command has actually run — the terminal echoes the typed
    # line verbatim first (literal, unexpanded "$?"), so matching on that echo
    # would report success before the command executed at all.
    c.send_input(b"touch /etc/ocode-terminal-adversarial-write-test 2>&1; echo TOUCH_RC_$?\n")
    output = _drain_until(c, lambda s: "TOUCH_RC_1" in s, timeout=8)
    assert "Read-only file system" in output
    assert "TOUCH_RC_1" in output

    c.send_input(b"timeout 3 curl -s -o /dev/null -w '%{http_code}' https://example.com; echo CURL_RC_$?\n")
    output2 = _drain_until(c, lambda s: "CURL_RC_7" in s, timeout=8)
    assert "CURL_RC_7" in output2  # curl: could not connect (empty netns)

    c.stop(force=True)
    t.join(timeout=15)


def test_untrusted_workspace_refused_before_daemon_spawns_anything(tmp_path: Path) -> None:
    sock = tmp_path / ".ocode" / "terminal" / "untrusted.sock"
    daemon = SessionDaemon(tmp_path, ["true"], sock, run_id="untrusted")
    with pytest.raises(WorkspaceNotTrustedError):
        daemon.run()
    assert not sock.exists()


def test_stop_via_daemon_escalates_for_unresponsive_shell(tmp_path: Path) -> None:
    # An explicit `trap '' TERM` ignores the signal deterministically, regardless
    # of timing — see test_session.py's equivalent test for why relying on
    # interactive bash's own (timing-dependent) SIGTERM-ignoring isn't reliable.
    command = ["bash", "-c", "trap '' TERM; echo READY; while true; do sleep 0.2; done"]
    daemon, t, sock = _start_daemon(tmp_path, command, "escalate", grace_seconds=1.5)
    c = TerminalClient(sock)
    scrollback = c.attach()
    if b"READY" not in scrollback:
        # Wait for the target to have actually registered its trap before
        # stopping it — otherwise this races the target's own startup rather
        # than testing whether escalation works.
        _drain_until(c, lambda s: "READY" in s, timeout=5)

    t0 = time.time()
    reply = c.stop(force=False)
    elapsed = time.time() - t0

    assert reply.get("escalated") is True
    assert elapsed < 15  # bounded, not hung forever

    t.join(timeout=15)
    assert not t.is_alive()


def test_cli_daemon_survives_launching_process_exit(tmp_path: Path) -> None:
    """The real cross-process persistence claim: start via the actual CLI
    subprocess, let that process exit, then attach from a brand-new client and
    prove the session is still alive and reachable."""
    env = dict(os.environ)
    src_root = Path(__file__).resolve().parents[1] / "src"
    sandbox_src = Path(__file__).resolve().parents[2] / "sandbox-workspace-trust-v3.1" / "src"
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in [str(src_root), str(sandbox_src), env.get("PYTHONPATH")] if p
    )

    subprocess.run(
        [sys.executable, "-m", "ocode_sandbox", "trust", str(tmp_path), "--actor", "cli-test"],
        env=env, check=True, capture_output=True,
    )

    start = subprocess.run(
        [sys.executable, "-m", "ocode_terminal", "start", str(tmp_path), "--run-id", "cli-persist", "--", "bash", "-i"],
        env=env, check=True, capture_output=True, text=True, timeout=15,
    )
    info = json.loads(start.stdout)
    sock = Path(info["socket_path"])

    for _ in range(50):
        if sock.exists():
            break
        time.sleep(0.1)
    assert sock.exists(), "daemon socket never appeared after the launching CLI process exited"

    c = TerminalClient(sock)
    c.attach()
    reply = c.stop(force=True)
    assert reply.get("type") in ("status", "exited")
