# Bite 4 — Professional Editor Foundation — v3.4

A real Monaco-editor-based code editor for OCode (local mode), per
`ocode-platform-spec/BITE_ROADMAP.md`. Builds on Bite 1's (`ocode_sandbox`)
unmodified workspace trust check; does not depend on Bites 2 or 3. See
`PLAN.md` for the bounded implementation plan, scope boundary (notably: no LSP
broker, no diagnostics/symbols/completion — explicitly deferred, not hidden),
and residual risks.

## What this is

A local HTTP server (`server/`, stdlib-only) serves a static frontend
(`frontend/`) built on the real `monaco-editor` npm package (vendored locally,
no runtime CDN dependency) and a small JSON file-service API confined to a
single trusted workspace: path-escape and symlink protection, atomic writes,
content-hash optimistic concurrency, and OCode's own protected metadata
directory hidden from the editor entirely. The frontend implements multi-tab
editing, split panes, a dirty-state indicator with `beforeunload` protection
and `localStorage`-based unsaved-change recovery, Monaco's built-in search and
replace, a real diff editor (live buffer vs. last-saved content), a
format-document action, and accessible (ARIA-labeled, keyboard-reachable) tabs
and toolbar.

## Setup

```bash
scripts/vendor_monaco.sh                    # npm-installs and vendors monaco-editor
pip install ../sandbox-workspace-trust-v3.1  # Bite 1 dependency
```

## Run it

```bash
python3 -m ocode_sandbox trust /path/to/workspace --actor "your-name"
PYTHONPATH=../sandbox-workspace-trust-v3.1/src python3 -m server /path/to/workspace
# -> http://127.0.0.1:<port>
```

## Tests and evidence

```bash
scripts/run_tests_and_evidence.sh
```

Runs the specification gate, vendors Monaco, a clean-environment install proof,
the full backend + Playwright (real headless Chromium) end-to-end test suite,
captures a representative screenshot, and a rollback proof, then writes
`evidence/OCODE_BITE04_PROFESSIONAL_EDITOR_FOUNDATION_EVIDENCE_MANIFEST.json`.

## Known gaps (see PLAN.md for detail)

- No LSP broker, diagnostics, symbols, rename, references, or completion — the
  largest deferred piece relative to the full platform spec's vision for this
  bite, called out explicitly rather than built as empty scaffolding ahead of
  need.
- No merge conflict UI; a stale save is rejected outright (409), not merged.
- No binary file viewer; binary files are refused with a clear message.
- Local HTTP server only, no auth beyond the trust check, localhost-bound.
