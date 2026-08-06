"""Assemble evidence/OCODE_BITE03_TASKS_RUNTIME_PROFILES_EVIDENCE_MANIFEST.json from
the actual exit codes and captured output of the run just performed by
run_tests_and_evidence.sh. Mirrors Bites 1 and 2's generator.
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
        "bite": "Bite 3 - Tasks and runtime profiles - v3.3",
        "generated_at": time.time(),
        "gates": {
            "specification_gate": {
                "command": "python3 scripts/ocode_spec_gate.py",
                "exit_code": gate_exit,
                "passed": gate_exit == 0,
            },
            "clean_environment_install": {
                "command": "tasks-v3.3/scripts/install_clean_env.sh",
                "exit_code": install_exit,
                "passed": install_exit == 0,
                "log_tail": tail("INSTALL_LOG"),
            },
            "adversarial_and_functional_tests": {
                "command": "python3 -m pytest tests/ -v (against the clean-installed package)",
                "exit_code": test_exit,
                "passed": test_exit == 0,
                "junit_summary": junit,
                "log_tail": tail("TEST_LOG"),
            },
            "rollback_demonstration": {
                "command": "tasks-v3.3/scripts/rollback_demo.sh",
                "exit_code": rollback_exit,
                "passed": rollback_exit == 0,
                "log_tail": tail("ROLLBACK_LOG"),
            },
        },
        "all_mandatory_gates_passed": all_pass,
        "truth_label": "LOCALLY_VERIFIED" if all_pass else "IMPLEMENTED_NOT_EXECUTED",
        "bugs_found_and_fixed_during_this_bite": [
            "Cancelling a still-QUEUED job only marked intent (a set membership) "
            "without transitioning its state; with all worker slots busy, the "
            "job could report QUEUED for an arbitrarily long time after being "
            "cancelled. Fixed: cancel() now removes a still-queued job from the "
            "queue and transitions it to CANCELLED synchronously.",
            "The job state machine didn't allow LEASED -> FAILED, only "
            "LEASED -> RUNNING/CANCELLED — so a job whose sandboxed process "
            "failed to even start (e.g. an untrusted workspace) crashed the "
            "worker thread trying to record that outcome. Fixed by adding the "
            "direct LEASED -> FAILED transition for exactly that case.",
        ],
        "residual_risks": [
            "Concurrency-limit enforcement is per-daemon-instance; normal CLI "
            "usage always targets one well-known socket path per workspace, so "
            "this is not reachable in practice, but is not enforced across "
            "hypothetical multiple daemon instances for the same workspace.",
            "No graceful cancellation (single hard kill of the sandboxed "
            "process tree) — a deliberate scope decision for batch/build/test "
            "jobs, not an oversight; see PLAN.md.",
            "Primitives verified inside this nested development container only, "
            "same caveat as Bites 1 and 2.",
        ],
        "next_eligible_bite": "Bite 4 - Professional editor foundation - v3.4 (not started)",
    }

    out_path = EVIDENCE_DIR / "OCODE_BITE03_TASKS_RUNTIME_PROFILES_EVIDENCE_MANIFEST.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"evidence manifest written: {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
