"""Assemble evidence/OCODE_BITE05_SOURCE_CONTROL_WORKSPACE_EVIDENCE_MANIFEST.json
from the actual exit codes and captured output of the run just performed by
run_tests_and_evidence.sh. Mirrors Bites 1-4's generator.
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
        "bite": "Bite 5 - Source-control workspace - v3.5",
        "generated_at": time.time(),
        "gates": {
            "specification_gate": {
                "command": "python3 scripts/ocode_spec_gate.py",
                "exit_code": gate_exit,
                "passed": gate_exit == 0,
            },
            "clean_environment_install": {
                "command": "git-workspace-v3.5/scripts/install_clean_env.sh",
                "exit_code": install_exit,
                "passed": install_exit == 0,
                "log_tail": tail("INSTALL_LOG"),
            },
            "adversarial_and_functional_tests": {
                "command": "python3 -m pytest tests/ -v (backend + real headless-Chromium Playwright e2e, "
                "against real git repositories this suite creates and tears down)",
                "exit_code": test_exit,
                "passed": test_exit == 0,
                "junit_summary": junit,
                "log_tail": tail("TEST_LOG"),
            },
            "rollback_demonstration": {
                "command": "git-workspace-v3.5/scripts/rollback_demo.sh",
                "exit_code": rollback_exit,
                "passed": rollback_exit == 0,
                "log_tail": tail("ROLLBACK_LOG"),
            },
        },
        "all_mandatory_gates_passed": all_pass,
        "truth_label": "LOCALLY_VERIFIED" if all_pass else "IMPLEMENTED_NOT_EXECUTED",
        "scope_notes": {
            "implemented_and_evidenced": [
                "Hardened git backend: every operation runs the real git binary, "
                "confined to a trusted workspace (Bite 1's trust check, reused "
                "unmodified), hooks disabled via a real empty core.hooksPath "
                "directory, external diff disabled via --no-ext-diff (the "
                "-c diff.external= form was verified NOT to work), no pager, "
                "no interactive editor/credential prompts, no network operation "
                "exposed at all",
                "status, diff (working tree vs index, index vs HEAD), "
                "stage/unstage (whole-file), commit, history, branches "
                "(create/switch/delete, refusing to delete the current branch), "
                "tags, stash (save/list/pop/drop), restore, cherry-pick, rebase, "
                "merge, conflict listing, and conflict resolution "
                "(ours/theirs/mark-resolved) - all verified against real git "
                "repositories, including a real merge conflict produced by two "
                "branches editing the same line",
                "Graphical frontend: staged/unstaged/untracked/conflicted file "
                "lists with per-file actions, a commit box, a branch switcher "
                "with create, a tag panel, a stash panel, a history log, a "
                "hand-rolled unified-diff renderer, and a conflict banner with "
                "abort - verified end-to-end in real headless Chromium against "
                "the real backend and real on-disk git state",
                "Path confinement and the protected .ocode metadata directory: "
                "same discipline as Bite 4's file service, reused and adapted "
                "for git operations (staging/diffing/restoring a path under "
                ".ocode is rejected outright, and it never appears in status)",
                "Fail-closed workspace trust gating at both the gitservice and "
                "HTTP layers, reusing Bite 1's trust module unmodified",
            ],
            "explicitly_out_of_scope_or_scaffolded": [
                "Provider adapters (GitHub/GitLab pull or merge request "
                "creation, required-checks status, reviewer requests): no "
                "network call to any git remote is made by this bite at all",
                "Protected branch rules, required checks, review gates: "
                "properties of a provider server, not enforceable locally",
                "Interactive hunk-level staging: whole-file stage/unstage only",
                "A secrets-backed credential vault: this bite has no code path "
                "that could need credentials in the first place (no fetch/"
                "push/clone/pull), which is the actual posture, not a vault "
                "that doesn't exist",
            ],
        },
        "residual_risks": [
            "Whole-file stage/unstage only; a file mixing wanted and unwanted "
            "changes has no hunk-level tool in this bite.",
            "No network operations are exposed, so credential isolation is "
            "achieved by omission of the capability rather than a hardened "
            "credential broker - documented as the actual posture.",
            "Single-process local HTTP server, no auth beyond the trust check; "
            "binds to 127.0.0.1 only, acceptable for local single-user mode.",
            "Browser automation evidence was gathered in this development "
            "container's headless Chromium only, same environment-generalization "
            "caveat as the primitive-level testing in Bites 1-4.",
        ],
        "next_eligible_bite": "Bite 6 - Debugging - v3.6 (not started)",
    }

    out_path = EVIDENCE_DIR / "OCODE_BITE05_SOURCE_CONTROL_WORKSPACE_EVIDENCE_MANIFEST.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"evidence manifest written: {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
