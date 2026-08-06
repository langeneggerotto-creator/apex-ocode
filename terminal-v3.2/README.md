# Bite 2 — Persistent Integrated Terminal — v3.2

Local-mode persistent, sandboxed, reconnectable terminal sessions for OCode, per
`ocode-platform-spec/BITE_ROADMAP.md`. Builds on Bite 1's (`ocode_sandbox`) trust,
cgroup, mount-isolation, and seccomp-exec primitives unchanged — see `PLAN.md` for
the bounded implementation plan, scope boundary, and residual risks.

## What this is

A persistent terminal **session** is a sandboxed, PTY-attached shell owned by a
small **daemon process** — separate from whatever CLI invocation started it, so the
session survives that process exiting (real "reconnect", not an in-process
simulation). Clients talk to the daemon over a local Unix domain socket (mode
0600) using a small, closed set of message types (attach, input, resize, detach,
stop, status) — never raw unrestricted PTY forwarding. A capped scrollback buffer
is replayed on attach; a capped input-event log and a JSON evidence record capture
what happened. Stop escalation sends SIGTERM to the sandboxed process directly,
waits a grace period, and escalates to SIGKILL if the target doesn't respond (many
real interactive programs, including plain interactive bash, ignore SIGTERM by
design — SIGKILL is the only signal guaranteed to work). An idle timeout and a
maximum session duration are enforced by the daemon automatically.

## Install

```bash
pip install ../sandbox-workspace-trust-v3.1  # Bite 1 dependency
pip install .
```

## CLI usage

```bash
python -m ocode_sandbox trust /path/to/workspace --actor "your-name"

python -m ocode_terminal start /path/to/workspace --run-id my-session -- bash
# -> {"run_id": "my-session", "socket_path": "/path/to/workspace/.ocode/terminal/my-session.sock"}

python -m ocode_terminal status <socket_path>
python -m ocode_terminal resize <socket_path> 120 40
python -m ocode_terminal send <socket_path> "echo hello"
python -m ocode_terminal stop <socket_path>
```

## Library usage

```python
from pathlib import Path
from ocode_terminal.client import TerminalClient

client = TerminalClient(Path("/path/to/workspace/.ocode/terminal/my-session.sock"))
scrollback = client.attach()
client.send_input(b"echo hello\n")
msg = client.read_message()  # {"type": "output", "data": "<base64>"}
client.stop()
```

## Tests and evidence

```bash
scripts/run_tests_and_evidence.sh
```

Runs the specification gate, a clean-environment install proof (Bite 1's package
plus this one), the full adversarial + functional test suite against the
clean-installed packages, and a rollback proof, then writes
`evidence/OCODE_BITE02_PERSISTENT_TERMINAL_EVIDENCE_MANIFEST.json`.

## Bugs found and fixed while building this bite

Several genuine concurrency/signal-handling bugs surfaced during implementation and
were fixed with regression tests before this bite was considered sealed — notably a
kernel-level PID-namespace-1 signal-immunity issue (fixed with a minimal
init/reaper shim, `_pty_init.py`) and a signal-handler-inheritance-across-fork()
race (fixed by blocking signals in the parent *before* forking, not after). See
`PLAN.md` and the generated evidence manifest for the full list and reasoning.

## Known gaps (see PLAN.md for detail)

- No network-reachable API — local Unix domain socket only.
- No authentication beyond filesystem permissions on the socket.
- Scrollback/input history are in-memory only, not persisted to disk.
- No supervision of the daemon process itself in local mode.
