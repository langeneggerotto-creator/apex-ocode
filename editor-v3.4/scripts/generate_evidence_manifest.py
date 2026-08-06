"""Assemble evidence/OCODE_BITE04_PROFESSIONAL_EDITOR_FOUNDATION_EVIDENCE_MANIFEST.json
from the actual exit codes and captured output of the run just performed by
run_tests_and_evidence.sh. Mirrors Bites 1-3's generator.
"""

from __future__ import annotations

import json
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path

EVIDENCE_DIR = Path(os.environ["EVIDENCE_DIR"])
JUNIT_XML = Path(os.environ["JUNIT_XML"])


def parse_junit(path: Path) -> dict:
    if not path.is_file():
        return {"available": False}
    tree = ET.parse(path)
    root = tree.getroot()
    suite = root.find("testsuite") if root.tag != "testsuite" else root
    if suite is None:
        return {"available": False}
    cases = []
    for case in suite.findall("testcase"):
        status = "passed"
        if case.find("failure") is not None:
            status = "failed"
        elif case.find("skipped") is not None:
            status = "skipped"
        elif case.find("error") is not None:
            status = "error"
        cases.append({"name": f"{case.get('classname')}::{case.get('name')}", "status": status})
    return {
        "available": True,
        "total": int(suite.get("tests", 0)),
        "failures": int(suite.get("failures", 0)),
        "errors": int(suite.get("errors", 0)),
        "skipped": int(suite.get("skipped", 0)),
        "cases": cases,
    }


def tail(path_env: str, n_chars: int = 4000) -> str:
    path = Path(os.environ[path_env])
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-n_chars:]


def main() -> int:
    gate_exit = int(os.environ["GATE_EXIT"])
    install_exit = int(os.environ["INSTALL_EXIT"])
    test_exit = int(os.environ["TEST_EXIT"])
    rollback_exit = int(os.environ["ROLLBACK_EXIT"])

    junit = parse_junit(JUNIT_XML)
    all_pass = gate_exit == 0 and install_exit == 0 and test_exit == 0 and rollback_exit == 0

    manifest = {
        "schema_version": "ocode.bite-evidence-manifest.v1",
        "bite": "Bite 4 - Professional editor foundation - v3.4",
        "generated_at": time.time(),
        "gates": {
            "specification_gate": {
                "command": "python3 scripts/ocode_spec_gate.py",
                "exit_code": gate_exit,
                "passed": gate_exit == 0,
            },
            "clean_environment_install": {
                "command": "editor-v3.4/scripts/install_clean_env.sh",
                "exit_code": install_exit,
                "passed": install_exit == 0,
                "log_tail": tail("INSTALL_LOG"),
            },
            "adversarial_and_functional_tests": {
                "command": "python3 -m pytest tests/ -v (backend + real headless-Chromium Playwright e2e)",
                "exit_code": test_exit,
                "passed": test_exit == 0,
                "junit_summary": junit,
                "log_tail": tail("TEST_LOG"),
            },
            "rollback_demonstration": {
                "command": "editor-v3.4/scripts/rollback_demo.sh",
                "exit_code": rollback_exit,
                "passed": rollback_exit == 0,
                "log_tail": tail("ROLLBACK_LOG"),
            },
        },
        "all_mandatory_gates_passed": all_pass,
        "truth_label": "LOCALLY_VERIFIED" if all_pass else "IMPLEMENTED_NOT_EXECUTED",
        "scope_notes": {
            "implemented_and_evidenced": [
                "Real monaco-editor integration (vendored from npm, no runtime CDN)",
                "Multi-tab per pane, independent models per tab",
                "Split panes (two independent editor groups)",
                "Unsaved-state dirty indicator, beforeunload guard, "
                "localStorage-based draft recovery across reload",
                "Search and replace (Monaco's built-in find/replace widget), "
                "verified with a real Replace-All producing the expected buffer",
                "Diff editor showing a real computed diff between live and "
                "last-saved content (not a static mock)",
                "Format-document action wired (JSON, via Monaco's built-in formatter)",
                "Accessibility: ARIA roles/labels on toolbar and tab strip, "
                "verified via a real accessibility-tree query in headless Chromium",
                "Backend file service: path-escape and symlink protection, "
                "protected-metadata-directory exclusion, atomic writes, "
                "content-hash optimistic concurrency, workspace-trust gating "
                "reusing Bite 1 unmodified",
            ],
            "explicitly_out_of_scope_or_scaffolded": [
                "Diagnostics and symbols: no language server exists; not wired "
                "to any real data source",
                "Rename, references, LSP-backed hover/completion, breadcrumbs: "
                "not implemented at all, not even as empty UI",
                "The LSP broker itself: not built (the single largest deferred "
                "piece relative to the full platform spec's vision for this bite)",
                "Merge conflict handling: not implemented",
                "Binary viewers: binary files are refused with a clear message, "
                "not rendered",
            ],
        },
        "residual_risks": [
            "Single-process local HTTP server, no auth beyond the trust check; "
            "binds to 127.0.0.1 only, acceptable for local single-user mode.",
            "Optimistic concurrency rejects a stale write outright rather than "
            "merging; the client must reload and reapply (deliberate scope "
            "decision, matches 'merge conflict handling' being out of scope).",
            "Vendored Monaco assets are not committed to git (restored "
            "deterministically by scripts/vendor_monaco.sh from a pinned "
            "npm version) — documented, not a hidden manual step.",
            "Browser automation evidence was gathered in this development "
            "container's headless Chromium only, same environment-generalization "
            "caveat as the primitive-level testing in Bites 1-3.",
        ],
        "next_eligible_bite": "Bite 5 - Source-control workspace - v3.5 (not started)",
    }

    out_path = EVIDENCE_DIR / "OCODE_BITE04_PROFESSIONAL_EDITOR_FOUNDATION_EVIDENCE_MANIFEST.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"evidence manifest written: {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
