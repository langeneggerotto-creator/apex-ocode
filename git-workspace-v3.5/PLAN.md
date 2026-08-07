# Bite 5 — Source-Control Workspace — v3.5 — Implementation Plan

Predecessor check: Bites 1–4 are sealed (implemented, tested, evidenced,
rollback-proven) on branches `claude/bite-01-sandbox-workspace-trust`,
`claude/bite-02-persistent-terminal`, `claude/bite-03-tasks-runtime-profiles`,
`claude/bite-04-professional-editor-foundation`. This branch is built on top of
Bite 4's. No mandatory gate is currently failing.

## Scope boundary

Per `ocode-platform-spec/BITE_ROADMAP.md`: "Graphical Git, staging, branch
lifecycle, history, tags, stash, conflicts, review checks, provider contracts,
and restore operations," and `FULL_PLATFORM_SPEC.md` §11: "status, diff, stage,
unstage, commit, history, branches, tags, stash, restore, cherry-pick, rebase,
merge, protected branch rules, required checks, review gates, provider adapters
for pull or merge requests, conflict resolution, and rollback points. Git
credentials must be isolated; hooks, external diff programs, text conversions,
prompts, and untrusted configuration are disabled unless explicitly authorized."

In scope (real, tested, evidenced, entirely local — no network/provider calls):
- **Hardened git backend**: every operation runs against the actual `git`
  binary (there is no substitute for real git semantics), confined to a
  trusted workspace (Bite 1's trust check, reused unmodified), with every
  invocation explicitly hardened per-call rather than relying on ambient
  config: hooks disabled (`core.hooksPath` pointed at a real empty,
  non-writable-by-the-repo directory — not the myth of an inline empty
  override, see Risks), external diff/merge tools disabled
  (`--no-ext-diff`, `GIT_EDITOR=true`, no interactive prompts:
  `GIT_TERMINAL_PROMPT=0` + `GIT_ASKPASS=` pointed at a script that always
  fails closed), no pager (`core.pager=cat` / `--no-pager`), and the
  repository's own config/aliases/includes are never trusted implicitly
  (every invocation passes explicit `-c` overrides for the settings that
  matter rather than reading whatever the repo's `.git/config` says).
- **Operations**: status, diff (working tree vs. index, index vs. HEAD),
  stage/unstage (whole file and, where git supports it cleanly, whole-file
  granularity — not interactive hunk staging, out of scope for this bite),
  commit, history (log with pagination), branches (list, create, switch,
  delete — refusing to delete the current branch), tags (list, create),
  stash (list, save, pop, drop), restore (discard working-tree changes to a
  path), cherry-pick, rebase, merge, and conflict listing after a merge/
  rebase/cherry-pick stops with conflicts.
- **Graphical frontend**: a real, browser-tested UI — staged/unstaged/
  untracked file lists with per-file stage/unstage, a commit box, a branch
  switcher with create, a history log, a **unified diff view** (lightweight
  hand-rolled colored-diff renderer — deliberately not a re-vendor of Bite
  4's Monaco; a unified diff is naturally text-shaped and GitHub-style
  colored-line rendering doesn't need a full editing engine), a stash
  panel, and a conflict view that lists conflicted files with "keep ours" /
  "keep theirs" / "mark resolved after manual edit" actions.

Explicitly out of scope, and represented (if at all) only as inert/disabled UI,
never as working functionality:
- **Provider adapters** (opening a GitHub/GitLab pull or merge request,
  reading required-checks status, requesting reviewers): needs network
  access, provider credentials, and an identity/authorization model this
  bite doesn't have — squarely later-bite territory (provider integration
  surfaces belong with Bite 12's "Extensions, integrations," and any PR
  review-gate concept needs Bite 10's identity/collaboration first). No
  network call to any git remote is made by this bite at all — every test
  and every operation is against local repositories only.
- **Protected branch rules, required checks, review gates**: these are
  properties of a *server* (GitHub/GitLab branch protection, CI status) —
  nothing to enforce locally without a provider connection. Not built.
- **Interactive hunk-level staging**: whole-file stage/unstage only; a
  hunk-picker is a meaningfully separate feature this bite doesn't attempt.
- **Text conversions** (`.gitattributes`-driven filters like `clean`/`smudge`)
  are left at git's default (off unless the repo already configures them) —
  this bite does not add new filter-execution surface, and does not
  specifically re-enable or harden filters beyond git's own defaults.

## Files

```
git-workspace-v3.5/
  PLAN.md, README.md
  server/
    __init__.py
    gitservice.py      # hardened subprocess wrapper: every operation, every
                        # explicit safety flag, workspace-confined
    httpserver.py         # stdlib HTTP server: serves the frontend + JSON API,
                           # gated on Bite 1 workspace trust (reused unmodified)
    __main__.py             # CLI: python -m server <workspace> [--port N]
  frontend/
    index.html
    src/ (app.js, api.js, diff.js, styles.css)
  scripts/
    run_tests_and_evidence.sh, install_clean_env.sh, rollback_demo.sh
  tests/
    test_gitservice.py     # backend: hardening + every operation, against
                            # real git repos this bite creates and destroys
    test_git_e2e.py           # Playwright, real headless Chromium
  evidence/
```

## Contracts

- `gitservice.run(workspace, args, **kw)` is the *only* place that shells out
  to `git`; every public operation goes through it, so the hardening flags
  live in exactly one place, not copy-pasted per operation.
- `gitservice.status(workspace) -> GitStatus` (staged/unstaged/untracked/
  conflicted file lists), `.diff(workspace, path, *, staged=False) -> str`,
  `.stage(workspace, paths)`, `.unstage(workspace, paths)`,
  `.commit(workspace, message) -> sha`, `.log(workspace, limit=50) ->
  [Commit]`, `.branches(workspace) -> [Branch]`,
  `.create_branch/.switch_branch/.delete_branch`, `.tags`/`.create_tag`,
  `.stash_list/.stash_save/.stash_pop/.stash_drop`, `.restore(workspace,
  path)`, `.cherry_pick(workspace, sha)`, `.rebase(workspace, onto)`,
  `.merge(workspace, branch)`, `.conflicted_files(workspace) -> [str]`,
  `.resolve(workspace, path, strategy)` where strategy is `ours`/`theirs`/
  `resolved` (the last just stages the already-manually-edited file).
- Same fail-closed contract as every prior bite: `WorkspaceNotTrustedError`
  before any git process is spawned; a `GitOperationError` wraps any
  non-zero git exit with its stderr, never silently swallowed.
- HTTP API mirrors Bite 4's shape: `GET /api/git/status`, `GET
  /api/git/diff?path=&staged=`, `POST /api/git/stage`, ... one endpoint per
  operation, all requiring the workspace to already be trusted.

## Risks

- **`-c diff.external=` does NOT disable an external diff tool** — verified
  empirically before writing any code: git treats the empty override as "run
  the empty string as the external diff command" and errors, it does not
  fall back to the built-in diff. The correct mechanism is the `--no-ext-diff`
  flag on the `diff` subcommand itself, which was verified to work. Recorded
  here so a future maintainer doesn't reintroduce the broken form.
- **`core.hooksPath` must point at a real, empty, non-writable-by-the-repo
  directory** — not `/dev/null` used loosely as a concept; the verified,
  correct value is a literal path to an empty directory outside the
  workspace (this bite creates one per-invocation under a scratch location,
  never inside the trusted workspace itself, so a malicious repo cannot
  populate it). `/dev/null` itself was verified to work as the value in this
  environment (git treats a hooksPath that isn't a directory as "no hooks
  found"), but a real empty directory is more portable and is what ships.
- **No credential isolation beyond suppression**: this bite disables
  interactive credential prompts (fail closed: a fetch/push needing
  credentials fails immediately rather than hanging or leaking a prompt into
  captured output) but does not implement a secrets-backed credential
  vault — that's Bite 9's "Secrets, previews, and deployment." Since this
  bite makes no network calls at all (no fetch/push/clone/pull operations
  are exposed), the credential-isolation requirement is satisfied by not
  having a code path that could need credentials in the first place, which
  is stronger than merely suppressing prompts — documented as the actual
  posture, not oversold as a vault that doesn't exist.
- **Whole-file stage/unstage only**: a repo with a large single file that
  mixes wanted and unwanted changes has no hunk-level tool in this bite;
  documented, not hidden.

## Tests

Backend (real git repositories created and torn down per test, no network):
1. Hooks are confirmed disabled: a repo with an executable `pre-commit` hook
   that would leave detectable evidence if it ran does not leave that
   evidence after a commit through this service.
2. External diff is confirmed disabled: a repo with `diff.external`
   configured to a command that would leave detectable evidence produces a
   normal unified diff, not external-tool output, and the external command
   never ran.
3. No pager/no hang: log and diff calls on a repo with `core.pager` set to a
   blocking command return promptly (bounded subprocess timeout as a second
   line of defense).
4. Status/stage/unstage/commit round trip against a real repo with staged,
   unstaged, and untracked files.
5. Diff correctness: a known one-line change produces the expected unified
   diff content.
6. Branch lifecycle: create, switch, delete (including refusing to delete
   the currently checked-out branch).
7. Tag creation and listing.
8. Stash save/list/pop round trip.
9. Restore discards an uncommitted change to a specific path only.
10. Cherry-pick applies a specific commit's changes onto another branch.
11. Rebase completes cleanly for a fast-forward-able case.
12. Merge conflict: two branches edited the same line; merging produces a
    conflict, `conflicted_files` lists exactly the conflicted path, and
    `resolve(..., "ours")` / `resolve(..., "theirs")` each produce the
    expected resulting content and clear the conflict.
13. Untrusted workspace: every operation refuses before spawning `git`.
14. Path confinement: an operation targeting a path outside the workspace
    (or reaching there via a symlink) is rejected, same discipline as
    Bite 4's file service.

Playwright, against the real backend and real git repos in headless Chromium:
15. Status view shows staged/unstaged/untracked correctly; staging a file via
    the UI moves it between lists.
16. Commit via the UI creates a real commit, visible in `git log` on disk.
17. Branch switch via the UI changes the actual checked-out branch on disk.
18. Diff view renders the real diff content for a modified file.
19. A real merge conflict (set up on disk before loading the page) shows the
    conflicted file in the UI; "keep ours" resolves it and the resulting
    commit reflects the chosen content.

## Evidence

`scripts/run_tests_and_evidence.sh`: specification gate, backend + Playwright
tests, a representative screenshot, and a rollback proof, writing
`evidence/OCODE_BITE05_SOURCE_CONTROL_WORKSPACE_EVIDENCE_MANIFEST.json`.
Bites 1–4's own gate scripts are re-run unmodified to confirm no regression.

## Rollback

Additive-only new top-level directory; nothing inside `sandbox-workspace-
trust-v3.1/`, `terminal-v3.2/`, `tasks-v3.3/`, or `editor-v3.4/` is touched.

## Truth label target

`LOCALLY_VERIFIED` for everything in scope above; provider adapters, protected
branch rules, required checks, and review gates are not claimed as working —
either absent entirely or, where a seam is genuinely useful to leave (none
identified for this bite — unlike Bite 4's diagnostics seam, there is no
"provider adapter interface" worth stubbing before a provider integration bite
defines what it actually needs).

## Next eligible bite (not started)

Bite 6 — Debugging — v3.6.
