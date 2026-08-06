# Bite 3 — Tasks and Runtime Profiles — v3.3

Declarative tasks, structured job states, and a concurrency-limited job manager for
OCode (local mode), per `ocode-platform-spec/BITE_ROADMAP.md`. Builds on Bite 1's
(`ocode_sandbox`) unmodified isolation primitives; does not depend on Bite 2
(`ocode_terminal`) — jobs are batch/non-interactive, not PTY sessions. See
`PLAN.md` for the bounded implementation plan, scope boundary, and residual risks.

## What this is

A **task manifest** (`.ocode/tasks.json` in the workspace) declares named tasks —
run, test, lint, format, type-check, build, preview, or migration — each with a
command, timeout, and optional resource-limit overrides. Submitting a task (or an
ad-hoc command) creates a **job** that moves through exactly the seven states
`FULL_PLATFORM_SPEC.md` §9 names: `queued -> leased -> running ->` one of
`succeeded | failed | cancelled | timed_out`. A per-workspace **job manager
daemon** (same persistent-process pattern as Bite 2's terminal daemon, reachable
over a local Unix domain socket) owns a bounded worker pool that enforces a
**concurrency limit** — jobs beyond the limit stay queued until a slot frees.
Cancelling a queued job marks it cancelled immediately; cancelling a running job
tears down its sandboxed process tree. Logs are captured, capped, and
secret-scrubbed; a JSON evidence record is written per job.

## Install

```bash
pip install ../sandbox-workspace-trust-v3.1  # Bite 1 dependency
pip install .
```

## CLI usage

```bash
python -m ocode_sandbox trust /path/to/workspace --actor "your-name"
python -m ocode_tasks start-daemon /path/to/workspace --concurrency 2

# Ad-hoc command:
python -m ocode_tasks submit /path/to/workspace --timeout 60 -- pytest -q

# Declared task (from .ocode/tasks.json):
python -m ocode_tasks submit /path/to/workspace --task test

python -m ocode_tasks status /path/to/workspace <job_id>
python -m ocode_tasks logs /path/to/workspace <job_id>
python -m ocode_tasks list /path/to/workspace
python -m ocode_tasks cancel /path/to/workspace <job_id>
python -m ocode_tasks shutdown /path/to/workspace
```

Manifest format (`.ocode/tasks.json`):

```json
{
  "tasks": {
    "test": {"type": "test", "command": ["pytest", "-q"], "timeout_seconds": 300},
    "lint": {"type": "lint", "command": ["ruff", "check", "."]}
  }
}
```

## Tests and evidence

```bash
scripts/run_tests_and_evidence.sh
```

Runs the specification gate, a clean-environment install proof (Bite 1's package
plus this one), the full adversarial + functional test suite against the
clean-installed packages, and a rollback proof, then writes
`evidence/OCODE_BITE03_TASKS_RUNTIME_PROFILES_EVIDENCE_MANIFEST.json`.

## Bugs found and fixed while building this bite

Two real state-machine bugs surfaced during implementation and were fixed with
regression tests: cancelling a still-queued job only marked intent without
actually transitioning its state (could report `queued` indefinitely under load),
and the state machine didn't allow a job whose process failed to even start to
move directly from `leased` to `failed`. See `PLAN.md` and the generated evidence
manifest for details.

## Known gaps (see PLAN.md for detail)

- No graceful cancellation — a single hard kill of the sandboxed process tree,
  a deliberate scope decision for batch/build/test jobs (unlike Bite 2's
  interactive-shell stop, which specifically needed gracefulness).
- No network-reachable API — local Unix domain socket only.
- `preview` and `migration` task types are accepted by the manifest schema as
  labels; this bite does not add preview-port-proxying or migration-specific
  execution semantics beyond running the declared command as a job.
