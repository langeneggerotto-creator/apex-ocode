"""Internal PID-1-of-namespace init/reaper shim.

Not shared with Bite 1 and does not modify anything in ``ocode_sandbox`` — Bite 1
never needed graceful signal delivery to the sandboxed process (its timeout path
always hard-kills), so this problem never surfaced there.

Bite 2 needs graceful SIGTERM-then-SIGKILL escalation. Per ``pid_namespaces(7)``,
the kernel refuses to deliver any signal with default disposition to a PID
namespace's process 1, *even if the signal's default action is "terminate"* —
regardless of what the target program would normally do with SIGTERM, if it never
explicitly installed a handler (the common case), the signal is silently dropped
as long as that program is process 1 of its namespace. Because ``unshare --pid
--fork`` combined with a chain of ``exec()`` calls (mount setup, ``setpriv``, the
seccomp-applying exec helper) never forks again, the final target process was
always ending up as PID 1 — immune to graceful stop.

The fix: fork once more here. This process (PID 1 of the namespace) becomes a
minimal init that installs real handlers for SIGTERM/SIGINT/SIGHUP/SIGQUIT and
forwards them to the child, and reaps zombies (including re-parented orphans). The
child applies the seccomp filter and execs the real target, landing on PID 2+,
where ordinary default-disposition signal handling applies normally.

A signal with default disposition delivered to a namespace's PID 1 is *dropped*,
not queued for later delivery — so the handlers above must be installed as early
as possible, and the caller needs a reliable way to know they're actually in place
before it can trust a subsequent SIGTERM to do anything. The mount/cgroup setup
script that runs *before* this program is even exec'd is itself PID 1 too, for its
whole duration, with no handler at all — a signal sent during that phase is lost
outright, no matter what this file does afterwards. The fix for that part: a
short, fixed-length readiness sentinel is written to stdout (the PTY) as literally
this program's first action; ``session.spawn()`` blocks on reading exactly that
sentinel before returning, so a caller can never observe a "successfully spawned"
session while any part of the earlier, handler-less setup phase could still be in
flight.

There is a second, easy-to-miss window: fork() itself. ``signal.signal()``
handlers are inherited across fork() — naively resetting them to default *inside*
the child, after ``os.fork()`` returns there, is not early enough. Signal dispatch
on resuming from fork() can happen as part of the child being scheduled, ahead of
any user-space bytecode at all — in particular, a signal the parent forwards to
the child's pid moments after fork() can be fully delivered and handled by the
kernel using the child's *inherited* (not yet reset) handler before the child
executes a single line of its own Python code. The fix here is to block the
forwarded signals in the *parent*, before calling fork() at all: fork() is atomic
at the kernel level, so the child inherits the blocked mask from the very instant
it exists, with no gap — nothing can be delivered to it via any disposition until
it explicitly unblocks, which it only does after resetting to SIG_DFL.
"""

from __future__ import annotations

import json
import os
import signal
import sys

from ocode_sandbox.seccomp_policy import apply_and_exec

FORWARDED_SIGNALS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT)
READY_SENTINEL = b"\x00OCODE_PTY_INIT_READY\x00"


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: _pty_init '<json-encoded argv list>'", file=sys.stderr)
        raise SystemExit(2)
    argv = json.loads(sys.argv[1])

    child_pid_box: list = [None]
    pending_signal_box: list = [None]

    def _forward(signum, _frame):  # noqa: ANN001
        child_pid = child_pid_box[0]
        if child_pid is None:
            # fork() hasn't returned yet; remember it and deliver as soon as the
            # real child PID is known, right after the fork() call below.
            pending_signal_box[0] = signum
            return
        try:
            os.kill(child_pid, signum)
        except ProcessLookupError:
            pass

    for sig in FORWARDED_SIGNALS:
        signal.signal(sig, _forward)

    stdout_fd = sys.stdout.fileno()
    written = 0
    while written < len(READY_SENTINEL):
        written += os.write(stdout_fd, READY_SENTINEL[written:])

    # See module docstring: blocking before fork (not after) is load-bearing.
    signal.pthread_sigmask(signal.SIG_BLOCK, FORWARDED_SIGNALS)
    child_pid = os.fork()
    if child_pid == 0:
        # Still blocked (inherited from the parent atomically at fork). Reset
        # dispositions to default now, then unblock — from this point, any
        # signal (including one that was already pending) is delivered using the
        # now-current default disposition, i.e. the process just terminates.
        # That is the correct outcome for an early signal, not silence.
        for sig in FORWARDED_SIGNALS:
            signal.signal(sig, signal.SIG_DFL)
        signal.pthread_sigmask(signal.SIG_UNBLOCK, FORWARDED_SIGNALS)
        apply_and_exec(argv)
        return  # unreachable: apply_and_exec always execs or raises

    # Parent: unblock immediately so _forward resumes handling signals normally.
    signal.pthread_sigmask(signal.SIG_UNBLOCK, FORWARDED_SIGNALS)
    child_pid_box[0] = child_pid
    if pending_signal_box[0] is not None:
        try:
            os.kill(child_pid, pending_signal_box[0])
        except ProcessLookupError:
            pass

    exit_code = 1
    while True:
        try:
            pid, status = os.waitpid(-1, 0)
        except ChildProcessError:
            break
        except InterruptedError:
            continue
        if pid == child_pid:
            if os.WIFEXITED(status):
                exit_code = os.WEXITSTATUS(status)
            elif os.WIFSIGNALED(status):
                exit_code = 128 + os.WTERMSIG(status)

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
