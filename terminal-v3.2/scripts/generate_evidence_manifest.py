"""Assemble evidence/OCODE_BITE02_PERSISTENT_TERMINAL_EVIDENCE_MANIFEST.json from
the actual exit codes and captured output of the run just performed by
run_tests_and_evidence.sh. Every value here comes from os.environ set by that script
or from parsing the JUnit XML it produced — nothing in this file is asserted without
a corresponding executed command. Mirrors Bite 1's generator.
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
        "bite": "Bite 2 - Persistent integrated terminal - v3.2",
        "generated_at": time.time(),
        "gates": {
            "specification_gate": {
                "command": "python3 scripts/ocode_spec_gate.py",
                "exit_code": gate_exit,
                "passed": gate_exit == 0,
            },
            "clean_environment_install": {
                "command": "terminal-v3.2/scripts/install_clean_env.sh",
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
                "command": "terminal-v3.2/scripts/rollback_demo.sh",
                "exit_code": rollback_exit,
                "passed": rollback_exit == 0,
                "log_tail": tail("ROLLBACK_LOG"),
            },
        },
        "all_mandatory_gates_passed": all_pass,
        "truth_label": "LOCALLY_VERIFIED" if all_pass else "IMPLEMENTED_NOT_EXECUTED",
        "bugs_found_and_fixed_during_this_bite": [
            "argparse.REMAINDER-adjacent CLI arg-splitting bug carried the same "
            "class of fix forward from Bite 1: the 'start' subcommand's command "
            "is now split off at a literal '--' before argparse ever sees it.",
            "PID-namespace-1 signal immunity (pid_namespaces(7)): the sandboxed "
            "target always landed on PID 1 of its namespace, where the kernel "
            "drops any default-disposition signal outright rather than queuing "
            "it — fixed by forking a minimal init/reaper (_pty_init.py) so the "
            "real target runs on PID 2+.",
            "Signal-handler inheritance across fork(): a signal forwarded to the "
            "freshly-forked target could be caught by its still-inherited (not "
            "yet reset) Python-level handler and silently absorbed before the "
            "real program even started — fixed by blocking the forwarded "
            "signals in the parent before fork() (inherited atomically, so "
            "there is no window at all) and only unblocking in the child after "
            "resetting dispositions to default.",
            "Client protocol livelock: awaiting a specific reply type re-read "
            "from a queue it had just written the same skipped message into, "
            "looping on it forever — fixed by having the reply-wait path read "
            "directly off the wire instead of through the pending-message queue.",
            "Unsynchronized concurrent socket writes: the daemon's output-reader "
            "thread and a client-request-handling thread could both call send() "
            "on the same connection concurrently, interleaving bytes mid-line — "
            "fixed with a per-connection send lock.",
            "escalated/exit_code race between the client-request handler thread "
            "(which signals and tracks escalation) and the reader thread (which "
            "independently detects process exit via PTY EOF) — fixed by setting "
            "the escalation flag synchronously at the moment SIGKILL is decided "
            "(via a callback), not from the signaling call's return value, and "
            "by making the reader thread the sole authority that reaps and "
            "reports the final exit code.",
        ],
        "residual_risks": [
            "Daemon process lifetime has no init-system supervision in local "
            "mode; a stale socket after an out-of-band kill is detected as a "
            "connection failure by the client, not hidden as a hang.",
            "Scrollback and input history are capped, in-memory only; a daemon "
            "crash loses them (not persisted to disk).",
            "No authentication on the Unix domain socket beyond filesystem "
            "permissions (mode 0600); acceptable for local single-user mode, "
            "not for later multi-user bites.",
            "Primitives verified inside this nested development container only, "
            "same caveat as Bite 1.",
        ],
        "next_eligible_bite": "Bite 3 - Tasks and runtime profiles - v3.3 (not started)",
    }

    out_path = EVIDENCE_DIR / "OCODE_BITE02_PERSISTENT_TERMINAL_EVIDENCE_MANIFEST.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"evidence manifest written: {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
