# Bite 4 — Professional Editor Foundation — v3.4 — Implementation Plan

Predecessor check: Bites 1–3 are sealed (implemented, tested, evidenced,
rollback-proven) on branches `claude/bite-01-sandbox-workspace-trust`,
`claude/bite-02-persistent-terminal`, `claude/bite-03-tasks-runtime-profiles`.
This branch is built on top of Bite 3's. No mandatory gate is currently failing.

## Scope boundary

Per `ocode-platform-spec/BITE_ROADMAP.md`: "Monaco integration, multiple tabs,
split panes, unsaved states, search and replace, diff editor, diagnostics,
symbols, formatting, accessibility, and recovery," and `FULL_PLATFORM_SPEC.md`
§8, which additionally names rename/references/hover/completion, a breadcrumb
outline, merge conflict handling, binary viewers, and "a Language Server
Protocol broker with isolated per-language processes."

This is a fundamentally different kind of bite than 1–3: a browser UI, not a
backend execution/isolation primitive. The scope split below is deliberate,
not an oversight — the LSP broker alone (spinning up per-language server
processes, isolating them, bridging JSON-RPC to the editor) is large enough to
be its own bounded unit of work, and the master prompt's rule against building
later-bite capability beyond the minimum interface applies here: this bite
builds the editor foundation for real, and provides the exact seams a future
LSP-integration bite plugs into, without building the broker itself.

In scope (real, browser-tested, evidenced):
- **Monaco Editor integration**: the actual `monaco-editor` package (vendored
  locally from npm — no runtime CDN dependency, matching the platform
  principle of local-first ownership), not a placeholder `<textarea>`.
- **Multi-tab**: open several files as tabs, switch, close (confirming on
  unsaved changes).
- **Split panes**: two independent editor groups side by side; a file can be
  opened into either.
- **Unsaved states**: a per-tab dirty indicator, a `beforeunload` guard, and
  **unsaved-change recovery** — edits are mirrored into `localStorage` and
  offered back on reload if the browser/tab closed before saving.
- **Search and replace**: Monaco's built-in find/replace widget, confirmed
  wired and functional, not just "present because Monaco has it."
- **Diff editor**: Monaco's built-in diff editor, showing the live in-memory
  buffer against the last-saved-on-disk content for the active file — a real,
  computed diff, not a static mock.
- **Formatting**: Monaco's built-in "Format Document" action wired to a real
  formatter for JSON (Monaco ships one) as the evidenced case; the format
  action dispatch point is generic (keyed by language id) so a later bite can
  register more formatters without redesigning anything here.
- **Accessibility**: keyboard-reachable tab bar and editor (Tab/arrow
  navigation), ARIA roles/labels on the tab strip and panes, verified with a
  real accessibility-tree snapshot in a headless browser, not asserted from
  reading the Monaco docs.
- **Backend file service**: a minimal local HTTP server — list/read/write,
  confined to a workspace that must carry Bite 1's trust marker (reused
  unmodified), path-escape and symlink protection, atomic writes, and
  content-hash-based optimistic concurrency (`FULL_PLATFORM_SPEC.md` §7
  language) so a save based on stale content is rejected rather than silently
  clobbering a concurrent change.

Explicitly out of scope, and represented (if at all) only as a `SCAFFOLDED`
interface with no behavior behind it, per `CLAUDE.md`'s truth-label rule:
- **Diagnostics and symbols**: the frontend exposes the seam (a function that,
  given a file, would apply Monaco markers / populate an outline) but it is
  never called with real data — no language server exists yet. Labeled
  `SCAFFOLDED` in the evidence, not claimed as working.
- **Rename, references, hover-from-LSP, completion-from-LSP, breadcrumbs**:
  not implemented at all (not even scaffolded) — these need the broker first
  and adding empty UI for them now would be exactly the "interface without
  behavior" the roadmap's scope-prohibition section warns against building
  ahead of need.
- **The LSP broker itself**: not built. This is the largest deferred piece;
  called out explicitly rather than left implicit.
- **Merge conflict handling, binary viewers**: not implemented. A binary file
  (detected via a null-byte sniff) is refused with a clear message rather than
  silently mangled by treating it as UTF-8 text.
- **Multi-user collaboration, presence, real-time sync**: out of scope (later
  identity/collaboration bites).

## Files

```
editor-v3.4/
  PLAN.md, README.md
  server/
    __init__.py
    fileservice.py     # confined list/read/write, path-escape + symlink
                        # protection, atomic write, content-hash concurrency
    httpserver.py        # stdlib-only HTTP server: serves static frontend +
                          # JSON file-service API, requires Bite 1 workspace
                          # trust before any operation
    __main__.py            # CLI: python -m server <workspace> [--port N]
  frontend/
    index.html
    src/
      app.js              # tabs, split panes, dirty state, recovery, wiring
      api.js               # fetch wrapper for the backend file-service API
      styles.css
    vendor/                 # monaco-editor npm package, vendored (git-ignored,
                             # restored by scripts/vendor_monaco.sh — matches
                             # how node_modules is normally not committed)
  scripts/
    vendor_monaco.sh        # npm-installs monaco-editor and copies its built
                             # min/vs assets into frontend/vendor/
    run_tests_and_evidence.sh, install_clean_env.sh, rollback_demo.sh
  tests/
    test_fileservice.py     # backend: path-escape, symlink, atomic write,
                             # concurrency conflict, untrusted workspace
    test_editor_e2e.py        # Playwright, real headless Chromium against the
                               # real backend + real Monaco
  evidence/
```

## Contracts

- `fileservice.list_tree(workspace) -> [RelPath]`, `.read(workspace, rel_path)
  -> (content, content_hash)`, `.write(workspace, rel_path, content, *,
  expected_hash=None) -> content_hash` — raises `PathEscapeError` for any
  resolved path outside the workspace (including through a symlink),
  `ConcurrencyConflictError` if `expected_hash` doesn't match the file's
  current on-disk hash, and the same `WorkspaceNotTrustedError` fail-closed
  contract as Bites 1–3 (reusing `ocode_sandbox.trust.verify_trust`
  unmodified).
- HTTP API: `GET /api/tree`, `GET /api/file?path=`, `PUT /api/file?path=` (body
  `{content, expected_hash}`), all requiring the workspace to already be
  trusted — the server never establishes trust itself, only checks it.
- Frontend `api.js` wraps these; `app.js` owns tab/pane/dirty state and the
  Monaco editor instances; nothing in the frontend writes to disk directly —
  every save goes through the same confined, hash-checked backend endpoint.

## Risks

- **No LSP-backed diagnostics/symbols/completion** — the single biggest gap
  relative to the full platform spec's vision for this bite; explicitly
  flagged, not hidden. A future bite adds the broker and wires it into the
  scaffolded seam this bite leaves in place.
- **Single-process HTTP server, no auth beyond trust check** — acceptable for
  local single-user mode (matches `SECURITY_DEPLOYMENT.md`); binds to
  localhost only, not exposed externally.
- **Optimistic concurrency is last-write-wins for the *check*, not a merge** —
  a conflicting save is rejected outright (the client must reload and reapply
  its edit) rather than attempting any automatic merge; simpler and safer than
  a partial merge implementation, and consistent with "merge conflict
  handling" being explicitly out of scope for this bite.
- **Vendored Monaco assets are not committed to git** (they're a few hundred
  MB of unpacked npm package content) — `scripts/vendor_monaco.sh` restores
  them deterministically from `package.json`'s pinned version; the install/
  test/evidence pipeline always runs it first, so this is not a hidden manual
  step.

## Tests

Backend (no browser needed):
1. Path escape via `../../etc/passwd`-style traversal is rejected.
2. Path escape via a symlink pointing outside the workspace is rejected.
3. Atomic write: a write either fully lands or the original file is
   untouched (simulated failure mid-write does not leave a partial file).
4. Concurrency conflict: a write with a stale `expected_hash` is rejected;
   the file is unchanged.
5. Untrusted workspace: every endpoint refuses before touching the
   filesystem.

Playwright, against the real backend and real Monaco in headless Chromium:
6. Open a file, edit it, see the dirty indicator, save, indicator clears.
7. Open a second file in a second tab, switch between tabs, content is
   correct and independent per tab.
8. Split pane: open a file into the second pane, edit independently of the
   first pane's copy.
9. Search and replace: find a string, replace it, buffer reflects the
   replacement.
10. Diff editor: edit a file, open the diff view, the rendered diff actually
    shows the changed line(s) (not just "the widget opened").
11. Unsaved-change recovery: edit without saving, reload the page, the draft
    is offered and restored from `localStorage`.
12. Accessibility: an accessibility-tree snapshot of the tab strip shows
    proper roles/names, and Tab-key navigation reaches the editor.

## Evidence

`scripts/run_tests_and_evidence.sh`: specification gate, Monaco vendoring,
backend tests, Playwright end-to-end tests (with at least one saved
screenshot as visual evidence), and a generated
`evidence/OCODE_BITE04_PROFESSIONAL_EDITOR_FOUNDATION_EVIDENCE_MANIFEST.json`.
Bites 1–3's own gate scripts are re-run unmodified to confirm no regression.

## Rollback

Additive-only new top-level directory; nothing inside `sandbox-workspace-
trust-v3.1/`, `terminal-v3.2/`, or `tasks-v3.3/` is touched. `git revert
<bite-4-commit>` removes it cleanly.

## Truth label target

`LOCALLY_VERIFIED` for everything in scope above; diagnostics/symbols/
completion/rename/references remain `SCAFFOLDED` or entirely absent, never
claimed as working.

## Next eligible bite (not started)

Bite 5 — Source-control workspace — v3.5.
