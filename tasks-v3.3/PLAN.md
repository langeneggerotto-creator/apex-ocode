# Bite 3 — Tasks and Runtime Profiles — v3.3 — Implementation Plan

Predecessor check: Bite 1 (`sandbox-workspace-trust-v3.1`) and Bite 2
(`terminal-v3.2`) are sealed — implemented, tested, evidenced, rollback-proven, on
branches `claude/bite-01-sandbox-workspace-trust` and
`claude/bite-02-persistent-terminal`. This branch is built on top of Bite 2's. No
mandatory gate is currently failing.

## Scope boundary

Per `ocode-platform-spec/BITE_ROADMAP.md`: "Declarative run, test, lint, format,
type-check, build, preview, and migration tasks; structured job states; logs;
cancellation; concurrency and resource policy," and
`FULL_PLATFORM_SPEC.md` §9: "Structured jobs shall move through queued, leased,
running, succeeded, failed, cancelled, and timed-out states... Output shall stream
over authenticated channels with resource quotas, timeouts, concurrency limits,
environment scrubbing, and evidence capture."

In scope (local mode):
- A **declarative task manifest** (`.ocode/tasks.json` in the workspace) naming
  tasks of type run/test/lint/format/type-check/build/preview/migration, each with
  a command, optional working directory (confined to the workspace), timeout, and
  resource limits.
- A **job**: one execution of a task (or an ad-hoc command), moving through
  exactly the seven states the spec names: `QUEUED -> LEASED -> RUNNING ->` one of
  `SUCCEEDED | FAILED | CANCELLED | TIMED_OUT`.
- A **job manager daemon** (same architecture as Bite 2's session daemon — a
  per-workspace background process reachable over a local Unix domain socket,
  bounded message protocol) owning a worker pool that enforces a **concurrency
  limit** (max N jobs running at once; excess submissions stay `QUEUED`).
- **Cancellation**: a queued job is marked `CANCELLED` without ever running; a
  running job is killed (its sandboxed process tree torn down) and marked
  `CANCELLED`.
- **Logs**: captured stdout+stderr per job, capped and secret-scrubbed (reusing
  Bite 1's `ocode_sandbox.evidence` helpers), retrievable by job id.
- **Evidence**: a JSON record per job (controls applied, timing, exit code, final
  state, resource usage) plus a manifest for the bite's own gates.
- Every job runs inside Bite 1's unmodified sandbox (trust check, namespaces,
  workspace-only write, network deny, capability drop, seccomp, cgroup limits) —
  this bite adds no new isolation primitive and does not touch
  `sandbox-workspace-trust-v3.1/`.

Out of scope, explicitly deferred:
- A PTY/interactive surface — tasks are batch/non-interactive by nature (pipes,
  like Bite 1's `run_sandboxed`, not Bite 2's PTY sessions). This bite does not
  depend on `ocode_terminal` at all.
- Preview process port detection / proxying (Bite 9, "Secrets, previews, and
  deployment") — a `preview` task type is accepted in the manifest schema as a
  labeled task type only; actually exposing/proxying a preview port is not
  implemented here.
- Migration *execution semantics* beyond "run this command" (transactional DB
  migration tooling, forward/backward pairing) — `migration` is a task type label
  the manifest accepts; this bite does not add migration-specific behavior beyond
  running the declared command as a job.
- Any network-reachable API — the job manager's socket is local-only, matching
  Bite 2's precedent, deferred to later control-plane bites.
- Cross-run job history persistence beyond the evidence directory (no database).

## Files

```
tasks-v3.3/
  PLAN.md, README.md, pyproject.toml, requirements.txt
  src/ocode_tasks/
    __init__.py
    manifest.py       # parse+validate .ocode/tasks.json
    job.py             # Job dataclass, JobState enum, transition validation
    executor.py         # non-blocking sandboxed job spawn/cancel, reusing
                         # ocode_sandbox.trust/cgroups/fs_isolation/_exec_helper
                         # exactly as Bite 1 does, but returning a handle
                         # immediately instead of blocking to completion
    protocol.py           # newline-delimited JSON framing (same pattern as Bite 2)
    manager.py              # JobManager: queue, worker pool, concurrency limit,
                             # state machine, cancellation, evidence
    daemon.py                 # JobDaemon: owns a JobManager, serves it over a
                               # Unix domain socket
    client.py                  # JobClient: submit/status/cancel/logs/list over
                                # the socket
    _daemon_main.py              # entrypoint the CLI backgrounds via Popen
    __main__.py                    # CLI: start-daemon/submit/status/cancel/logs/list
  tests/
    test_manifest.py
    test_executor.py
    test_manager_daemon.py
  scripts/
    run_tests_and_evidence.sh, install_clean_env.sh, rollback_demo.sh
  evidence/
```

## Contracts

- `manifest.load(workspace) -> TaskManifest` (dict of task name -> `TaskSpec`).
  Fails closed on malformed manifests (raises, does not silently ignore bad
  entries).
- `executor.start(workspace, command, *, limits, timeout_seconds) -> RunningJob`
  — same trust-check/seccomp-availability fail-closed contract as Bite 1's
  `run_sandboxed`, but does not block: spawns reader threads for stdout/stderr and
  returns immediately so a caller (the manager's worker) can poll or cancel.
- `executor.cancel(running: RunningJob) -> None` — kills the outer sandbox wrapper
  process; `--kill-child=SIGKILL` (already proven in Bite 1) tears down the whole
  process-namespace subtree. Deliberately a single hard kill, not a graceful
  SIGTERM-then-escalate: batch/build/test tooling does not need interactive
  grace the way Bite 2's shells did, and a single deterministic teardown avoids
  partial-cleanup states. Documented as a scope decision, not an oversight.
- `JobManager.submit(...) -> job_id`, `.status(job_id) -> Job`,
  `.cancel(job_id) -> bool`, `.logs(job_id) -> bytes`, `.list() -> [Job]`. State
  transitions are validated (e.g. cannot cancel an already-`SUCCEEDED` job) and
  rejected with a clear error rather than silently accepted.
- Daemon protocol mirrors Bite 2's exactly (newline-delimited JSON, bounded
  message types: `submit`, `status`, `cancel`, `logs`, `list`), reusing the same
  hardening (per-connection send lock, `MAX_LINE_BYTES` cap).

## Risks

- **Concurrency-limit enforcement is per-daemon-instance, not cross-daemon**: if
  a workspace somehow ends up with two job-manager daemons (should not happen in
  normal CLI use, which reuses one daemon per workspace via a well-known socket
  path), the limit would not be shared between them. Documented, not silently
  assumed away; normal CLI usage (`python -m ocode_tasks submit ...`) always
  targets the one daemon at the workspace's well-known socket path.
- **No graceful cancellation** (see contracts above) — a job that holds an
  external resource (e.g. a lock file outside the workspace, which the sandbox's
  read-only-except-workspace filesystem already limits the blast radius of) could
  in principle be interrupted mid-write to a workspace file; this is the same
  risk profile as any hard process kill (e.g. `kill -9`), not something this bite
  introduces.
- **Worker-pool threads and Python's GIL**: the manager uses OS threads per
  concurrency slot, each blocked in a blocking wait on its own subprocess — this
  is safe (each thread's blocking C call releases the GIL) and is the same
  pattern Bite 2's daemon already uses successfully.

## Tests

Unit: manifest parsing (valid + malformed, fails closed), job state-transition
validation (rejects invalid transitions).

Adversarial + functional (daemon+client, real sandboxed jobs):
1. Concurrency limit enforced: submit more jobs than the limit; excess stay
   `QUEUED` until a running slot frees, then transition to `LEASED`/`RUNNING`.
2. Cancel a queued job: never transitions to `RUNNING`, ends `CANCELLED`.
3. Cancel a running job: process torn down, transitions to `CANCELLED` within a
   bounded window (not hung).
4. Timeout: a job whose command runs longer than its configured timeout is killed
   and transitions to `TIMED_OUT`, not `FAILED` or hung.
5. Isolation still enforced inside a job: network egress denied, filesystem write
   outside the workspace denied — proving this bite didn't bypass Bite 1's
   controls.
6. Untrusted workspace: daemon refuses to run any job against an untrusted
   workspace.
7. Logs captured, capped, and secret-scrubbed; retrievable by job id after the
   job completes.

Functional (positive path): submit a declared manifest task, observe it reach
`SUCCEEDED` with the expected exit code and log output.

## Evidence

`scripts/run_tests_and_evidence.sh` mirrors Bites 1 and 2's: specification gate,
clean install proof (Bite 1's package plus this one), the full test suite against
the clean install, rollback proof, and a generated
`evidence/OCODE_BITE03_TASKS_RUNTIME_PROFILES_EVIDENCE_MANIFEST.json`. Bites 1 and
2's own gate scripts are re-run unmodified to confirm no regression.

## Rollback

Additive-only new top-level directory, same pattern as Bites 1 and 2: pip
uninstall proof plus `git revert <bite-3-commit>` removing the directory with
nothing else depending on it — no files inside `sandbox-workspace-trust-v3.1/` or
`terminal-v3.2/` are touched by this bite.

## Truth label target

`LOCALLY_VERIFIED`, same basis as Bites 1 and 2.

## Next eligible bite (not started)

Bite 4 — Professional editor foundation — v3.4.
