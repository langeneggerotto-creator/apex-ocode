#!/usr/bin/env bash
# Runs the full Bite 3 gate: spec gate, clean install proof (Bite 1 dependency +
# Bite 3), adversarial + functional test suite, and rollback proof — then writes a
# single evidence manifest capturing exact commands and outcomes.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="$BITE_DIR/evidence"
mkdir -p "$EVIDENCE_DIR"

echo "== 1/4 specification gate =="
( cd "$REPO_ROOT" && python3 scripts/ocode_spec_gate.py )
GATE_EXIT=$?

echo "== 2/4 clean-environment install proof =="
INSTALL_LOG="$EVIDENCE_DIR/.install_log.txt"
bash "$BITE_DIR/scripts/install_clean_env.sh" > "$INSTALL_LOG" 2>&1
INSTALL_EXIT=$?
cat "$INSTALL_LOG"

echo "== 3/4 test suite (clean-installed package) =="
VENV_DIR=$(tail -1 "$INSTALL_LOG")
"$VENV_DIR/bin/pip" install -q pytest
TEST_LOG="$EVIDENCE_DIR/.test_log.txt"
JUNIT_XML="$EVIDENCE_DIR/.junit.xml"
( cd "$BITE_DIR" && "$VENV_DIR/bin/python3" -m pytest tests/ -v --junitxml="$JUNIT_XML" ) | tee "$TEST_LOG"
TEST_EXIT=${PIPESTATUS[0]}

echo "== 4/4 rollback proof =="
ROLLBACK_LOG="$EVIDENCE_DIR/.rollback_log.txt"
bash "$BITE_DIR/scripts/rollback_demo.sh" > "$ROLLBACK_LOG" 2>&1
ROLLBACK_EXIT=$?
cat "$ROLLBACK_LOG"

echo "== assembling evidence manifest =="
GATE_EXIT="$GATE_EXIT" INSTALL_EXIT="$INSTALL_EXIT" TEST_EXIT="$TEST_EXIT" \
ROLLBACK_EXIT="$ROLLBACK_EXIT" TEST_LOG="$TEST_LOG" JUNIT_XML="$JUNIT_XML" \
INSTALL_LOG="$INSTALL_LOG" ROLLBACK_LOG="$ROLLBACK_LOG" EVIDENCE_DIR="$EVIDENCE_DIR" \
python3 "$BITE_DIR/scripts/generate_evidence_manifest.py"
MANIFEST_EXIT=$?

rm -f "$TEST_LOG" "$INSTALL_LOG" "$ROLLBACK_LOG" "$JUNIT_XML"

echo "== summary =="
echo "spec gate exit:      $GATE_EXIT"
echo "install proof exit:  $INSTALL_EXIT"
echo "test suite exit:     $TEST_EXIT"
echo "rollback proof exit: $ROLLBACK_EXIT"

if [ "$GATE_EXIT" -ne 0 ] || [ "$INSTALL_EXIT" -ne 0 ] || [ "$TEST_EXIT" -ne 0 ] || [ "$ROLLBACK_EXIT" -ne 0 ] || [ "$MANIFEST_EXIT" -ne 0 ]; then
    echo "BITE 3 GATES: FAIL"
    exit 1
fi
echo "BITE 3 GATES: PASS"
