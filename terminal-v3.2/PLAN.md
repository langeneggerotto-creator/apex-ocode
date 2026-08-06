# Bite 2 — Persistent Integrated Terminal — v3.2 — Implementation Plan

Predecessor check: Bite 1 (`sandbox-workspace-trust-v3.1`) is sealed — implemented,
tested (18/18 passing against a clean install), evidenced, and rollback-proven on
branch `claude/bite-01-sandbox-workspace-trust`. This branch (`claude/bite-02-...`)
is built on top of it. No mandatory gate is currently failing, so starting Bite 2 is
permitted per `ocode-platform-spec/BITE_ROADMAP.md`'s entry gates.

## Scope boundary

In scope (local mode, matching `SECURITY_DEPLOYMENT.md`'s single-user Linux sandbox
worker, and `BITE_ROADMAP.md`'s "Sandboxed PTY sessions, resize, reconnect,
scrollback, command history, stop escalation, timeout, streaming, terminal
evidence, and mobile-safe controls"):

- A persistent terminal **session** = a sandboxed PTY-attached shell, isolated with
  the exact same controls as Bite 1 (namespaces, workspace-only write, hidden
  metadata, network deny, capability drop, seccomp, cgroup limits) — this bite adds
  no new isolation primitives, it reuses Bite 1's `ocode_sandbox.trust`,
  `ocode_sandbox.cgroups`, `ocode_sandbox.fs_isolation`, and
  `ocode_sandbox._exec_helper` unchanged.
- A small **daemon process per session** that owns the PTY master fd and the
  sandboxed child, so the session survives the CLI process that started it exiting —
  this is what makes "reconnect" real rather than an in-process simulation.
- A **Unix domain socket protocol** (local mode only, no network exposure) for
  attach, input, resize, detach, stop, and status — bounded message types only,
  never raw unrestricted PTY forwarding, so the same contract can later be exposed
  safely to a mobile control surface (Bite 12) without redesign.
- **Scrollback**: a capped in-memory ring buffer replayed to a client on attach.
- **Command history**: a capped, scrubbed log of input events (for evidence/audit,
  not a readline-style history file).
- **Stop escalation**: SIGTERM to the sandboxed shell's real (host-visible) PID,
  with a grace period, then SIGKILL; `unshare --kill-child=SIGKILL` remains as a
  safety net if the daemon itself dies unexpectedly.
- **Timeouts**: idle timeout (no output and no input for N seconds) and a maximum
  session duration, both enforced by the daemon, both going through the same
  escalation path.
- **Terminal evidence**: a JSON record per session (reusing Bite 1's
  `ocode_sandbox.evidence` scrub/cap/write helpers) capturing controls applied,
  resize events, input/output byte counts, stop reason, and exit code.

Out of scope (deferred to later bites, not implemented even partially beyond the
minimum interface needed here):
- Any network-reachable API/WebSocket surface (Bite 7/10 control-plane concern) —
  the socket is a local Unix domain socket only, mode 0600, under the workspace's
  `.ocode` directory.
- Authentication/authorization beyond filesystem permissions on the socket (Bite 10
  identity/collaboration).
- Actual mobile UI (Bite 12) — only the bounded protocol contract that a mobile
  client could safely speak is built here.
- Declarative task/job runner (Bite 3) — this is an interactive shell session, not a
  structured build/test/lint job.

## Files

```
terminal-v3.2/
  PLAN.md, README.md, pyproject.toml, requirements.txt
  src/ocode_terminal/
    __init__.py
    session.py        # spawn a sandboxed PTY process (reuses Bite 1 primitives),
                       # discover its real child PID via /proc/<pid>/task/<pid>/children,
                       # graceful-then-forced stop escalation
    protocol.py        # newline-delimited JSON message framing shared by daemon+client
    daemon.py           # SessionDaemon: owns pty+child, scrollback ring buffer, input
                        # history, UDS server, idle/max-duration watchdog, evidence
    client.py            # TerminalClient: attach/input/resize/detach/stop/status over UDS
    _daemon_main.py       # `python -m ocode_terminal._daemon_main <args>` entry the CLI
                          # backgrounds via Popen(start_new_session=True) so the daemon
                          # outlives the CLI invocation that started it
    __main__.py            # CLI: start/attach/send/resize/stop/status
  tests/
    test_session.py        # unit: child-pid discovery, escalation (graceful + forced)
    test_daemon_client.py    # adversarial + functional: reconnect, scrollback, resize,
                              # idle timeout, isolation still enforced, untrusted refused
  scripts/
    run_tests_and_evidence.sh, install_clean_env.sh, rollback_demo.sh
  evidence/
```

## Contracts

- `session.spawn(workspace, command, *, cols, rows, limits) -> SpawnedSession`
  (`master_fd`, `outer_proc`, `child_pid`, `controls_applied`). Raises the same
  `WorkspaceNotTrustedError`/seccomp-unavailable failures as Bite 1 — fail closed,
  unchanged.
- `session.stop(spawned, *, grace_seconds=5, force=False) -> StopResult` — SIGTERM to
  `child_pid`, wait up to `grace_seconds`, SIGKILL if still alive; `force=True` skips
  straight to SIGKILL.
- Daemon UDS protocol, one JSON object per line, `base64`-encoded byte payloads:
  client → daemon: `attach`, `input`, `resize`, `detach`, `stop`, `status`;
  daemon → client: `scrollback` (once, on attach), `output` (live), `exited`,
  `status`, `error`. Unknown message types get an `error` reply, not a crash.
- `TerminalClient` wraps the protocol with a plain Python API for the CLI and tests.

## Risks

- **Daemon process lifetime**: the daemon is a plain background process (no init
  system supervision in local mode). If the host reboots or the daemon is killed
  out-of-band, the socket file can go stale. `client.py` treats a connection
  failure to an existing socket path as "session gone" and the CLI reports that
  rather than hanging — documented, not silently masked.
- **Child-PID discovery race**: reading
  `/proc/<unshare_pid>/task/<unshare_pid>/children` immediately after `Popen`
  can race the fork; `session.py` retries with a bounded backoff and raises a
  clear error if the child never appears, rather than signalling the wrong PID.
- **Scrollback/history are capped and in-memory only**: a daemon crash loses
  scrollback. Persisting it to disk is not attempted here (would add a new
  protected-metadata write surface); flagged as a residual gap.
- **No authentication on the UDS socket beyond filesystem permissions** (0600,
  owned by the invoking user) — acceptable for local single-user mode per
  `SECURITY_DEPLOYMENT.md`; multi-user access control is a later-bite concern.

## Tests

Unit: child-PID discovery, graceful stop (SIGTERM honored), forced stop escalation
(SIGTERM ignored → SIGKILL), untrusted workspace refused before any process spawns.

Adversarial + functional (daemon+client, real UDS, real sandboxed PTY):
1. Reconnect: start a session, write input, detach, attach again from a fresh
   client — scrollback replay includes the earlier output.
2. Resize: client resize call changes the PTY's actual `TIOCGWINSZ` as observed by
   the shell (`stty size`).
3. Idle timeout: a session with no input/output for longer than the configured
   idle timeout is stopped by the daemon automatically.
4. Isolation still holds inside a terminal session: network egress denied, write
   outside workspace denied — proving Bite 2 didn't bypass Bite 1's controls by
   routing through a PTY instead of pipes.
5. Untrusted workspace: `session.spawn` against a workspace with no trust marker
   raises before any process is created.
6. Stop escalation via the daemon: a client `stop` request against an
   unresponsive (SIGTERM-ignoring) shell still terminates the session within the
   grace-period + escalation window.

## Evidence

`scripts/run_tests_and_evidence.sh` mirrors Bite 1's: specification gate, clean
install proof (this package plus its local dependency on `ocode-sandbox`), the full
test suite against the clean install, rollback proof, and a generated
`evidence/OCODE_BITE02_PERSISTENT_TERMINAL_EVIDENCE_MANIFEST.json`.

## Rollback

Additive-only new top-level directory, same pattern as Bite 1:
`scripts/rollback_demo.sh` performs a clean `pip uninstall` proof;
`git revert <bite-2-commit>` removes the directory with nothing else depending on
it (Bite 1's package is untouched — no files inside `sandbox-workspace-trust-v3.1/`
are modified by this bite).

## Truth label target

`LOCALLY_VERIFIED`, same basis as Bite 1.

## Next eligible bite (not started)

Bite 3 — Tasks and runtime profiles — v3.3.
