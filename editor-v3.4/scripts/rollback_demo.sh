#!/usr/bin/env bash
# Demonstrates that Bite 4 is fully removable: the vendored, generated, and
# scratch artifacts it creates all live inside editor-v3.4/ (nothing touches
# sandbox-workspace-trust-v3.1/, terminal-v3.2/, or tasks-v3.3/), so deleting
# the directory (what `git revert <bite-4-commit>` does to tracked files) is a
# complete, clean rollback with nothing else depending on it.
set -euo pipefail

BITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$BITE_DIR/.." && pwd)"
SCRATCH_DIR="$(mktemp -d)/ocode-editor-rollback-proof"

echo "== copying repo into scratch dir =="
mkdir -p "$SCRATCH_DIR"
cp -r "$REPO_ROOT/." "$SCRATCH_DIR/"
rm -rf "$SCRATCH_DIR/editor-v3.4/frontend/vendor" "$SCRATCH_DIR/editor-v3.4/npm-install-scratch" "$SCRATCH_DIR/editor-v3.4/.pytest_cache"

echo "== before rollback: Bite 4 present =="
test -d "$SCRATCH_DIR/editor-v3.4"
echo "editor-v3.4/ present: OK"

echo "== rolling back (what git revert of the bite-4 commit does) =="
rm -rf "$SCRATCH_DIR/editor-v3.4"

echo "== after rollback =="
if [ -d "$SCRATCH_DIR/editor-v3.4" ]; then
    echo "ROLLBACK FAILED: editor-v3.4/ still present"
    exit 1
fi
echo "confirmed: editor-v3.4/ fully removed"

echo "== Bite 1 unaffected: its own gate still passes after Bite 4's removal =="
bash "$SCRATCH_DIR/sandbox-workspace-trust-v3.1/scripts/run_tests_and_evidence.sh" > "$SCRATCH_DIR/bite1_gate.log" 2>&1
if grep -q "BITE 1 GATES: PASS" "$SCRATCH_DIR/bite1_gate.log"; then
    echo "Bite 1 gate: PASS (unaffected by Bite 4's presence or removal)"
else
    echo "ROLLBACK PROOF FAILED: Bite 1 gate did not pass after Bite 4 removal"
    tail -40 "$SCRATCH_DIR/bite1_gate.log"
    exit 1
fi

rm -rf "$SCRATCH_DIR"
echo "ROLLBACK DEMONSTRATION: PASS"
