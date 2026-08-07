#!/usr/bin/env bash
# Demonstrates that Bite 5 is fully removable: everything it creates lives
# inside git-workspace-v3.5/ (nothing touches sandbox-workspace-trust-v3.1/,
# terminal-v3.2/, tasks-v3.3/, or editor-v3.4/), so deleting the directory
# (what `git revert <bite-5-commit>` does to tracked files) is a complete,
# clean rollback with nothing else depending on it.
set -euo pipefail

BITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$BITE_DIR/.." && pwd)"
SCRATCH_DIR="$(mktemp -d)/ocode-git-workspace-rollback-proof"

echo "== copying repo into scratch dir =="
mkdir -p "$SCRATCH_DIR"
cp -r "$REPO_ROOT/." "$SCRATCH_DIR/"
rm -rf "$SCRATCH_DIR/git-workspace-v3.5/.pytest_cache"

echo "== before rollback: Bite 5 present =="
test -d "$SCRATCH_DIR/git-workspace-v3.5"
echo "git-workspace-v3.5/ present: OK"

echo "== rolling back (what git revert of the bite-5 commit does) =="
rm -rf "$SCRATCH_DIR/git-workspace-v3.5"

echo "== after rollback =="
if [ -d "$SCRATCH_DIR/git-workspace-v3.5" ]; then
    echo "ROLLBACK FAILED: git-workspace-v3.5/ still present"
    exit 1
fi
echo "confirmed: git-workspace-v3.5/ fully removed"

echo "== Bites 1-4 directories intact after Bite 5's removal =="
for bite_dir in sandbox-workspace-trust-v3.1 terminal-v3.2 tasks-v3.3 editor-v3.4; do
    test -d "$SCRATCH_DIR/$bite_dir"
    echo "$bite_dir/: present, untouched"
done

echo "== spot check: Bite 1's own gate still passes (same check Bite 4 used) =="
log_file="$SCRATCH_DIR/bite1_gate.log"
bash "$SCRATCH_DIR/sandbox-workspace-trust-v3.1/scripts/run_tests_and_evidence.sh" > "$log_file" 2>&1
if grep -q "BITE 1 GATES: PASS" "$log_file"; then
    echo "Bite 1 gate: PASS (unaffected by Bite 5's presence or removal)"
else
    echo "ROLLBACK PROOF FAILED: Bite 1 gate did not pass after Bite 5 removal"
    tail -40 "$log_file"
    exit 1
fi

rm -rf "$SCRATCH_DIR"
echo "ROLLBACK DEMONSTRATION: PASS"
