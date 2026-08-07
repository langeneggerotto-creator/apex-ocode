# Bite 5 — Source-Control Workspace — v3.5

A real, hardened git backend and a graphical source-control UI for OCode
(local mode), per `ocode-platform-spec/BITE_ROADMAP.md`. Builds on Bite 1's
(`ocode_sandbox`) unmodified workspace trust check; does not depend on Bites
2, 3, or 4. See `PLAN.md` for the bounded implementation plan, scope boundary
(notably: no provider adapters, no protected-branch/required-check/review-gate
enforcement, no hunk-level staging — all explicitly deferred, not hidden),
and residual risks.

## What this is

A local HTTP server (`server/`, stdlib-only) serves a static frontend
(`frontend/`, plain JS — no build step) and a JSON API confined to a single
trusted workspace, backed by a hardened wrapper (`server/gitservice.py`)
around the real `git` binary: hooks disabled, external diff/pager/editor/
credential-prompt surface disabled, path-escape and symlink protection, and
OCode's own protected metadata directory (`.ocode/`) hidden from every git
operation. The frontend implements staged/unstaged/untracked/conflicted file
lists with per-file actions, a commit box, a branch switcher with create, a
tags panel, a stash panel, a history log, a hand-rolled unified-diff
renderer, and a conflict-resolution flow (keep ours / keep theirs / mark
resolved) with an abort action covering merge, rebase, and cherry-pick.

## Setup

```bash
pip install ../sandbox-workspace-trust-v3.1  # Bite 1 dependency
```

## Run it

```bash
python3 -m ocode_sandbox trust /path/to/git/repo --actor "your-name"
PYTHONPATH=../sandbox-workspace-trust-v3.1/src python3 -m server /path/to/git/repo
# -> http://127.0.0.1:<port>
```

`/path/to/git/repo` must already be a real git repository (`git init`) as
well as a trusted OCode workspace — this bite never runs `git init` itself.

## Tests and evidence

```bash
scripts/run_tests_and_evidence.sh
```

Runs the specification gate, a clean-environment install proof, the full
backend + Playwright (real headless Chromium) end-to-end test suite against
real git repositories, captures a representative screenshot, and a rollback
proof, then writes
`evidence/OCODE_BITE05_SOURCE_CONTROL_WORKSPACE_EVIDENCE_MANIFEST.json`.

## Known gaps (see PLAN.md for detail)

- No provider adapters (GitHub/GitLab pull or merge request creation,
  required-checks status, reviewer requests) — no network call to any git
  remote is made by this bite at all.
- No protected branch rules, required checks, or review gates — these are
  properties of a provider server, not enforceable locally.
- Whole-file stage/unstage only; no interactive hunk-level staging.
- No credential vault; this bite has no code path that needs credentials in
  the first place (no fetch/push/clone/pull is exposed).
- Local HTTP server only, no auth beyond the trust check, localhost-bound.
