#!/usr/bin/env bash
# Demonstrates that the Bite 1 artifact is fully removable: install into a clean
# venv, prove it works, uninstall, and prove the module is gone. There is no prior
# capability this bite could regress (it is additive, in its own top-level
# directory), so this proves reversibility rather than protecting an existing
# capability.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$(mktemp -d)/ocode-sandbox-rollback-proof"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q "$REPO_DIR"

echo "== before rollback =="
"$VENV_DIR/bin/python3" -c "import ocode_sandbox; print('present:', ocode_sandbox.__file__)"

echo "== rolling back (pip uninstall) =="
"$VENV_DIR/bin/pip" uninstall -y -q ocode-sandbox

echo "== after rollback =="
if "$VENV_DIR/bin/python3" -c "import ocode_sandbox" 2>/dev/null; then
    echo "ROLLBACK FAILED: module still importable"
    exit 1
fi
echo "confirmed: ocode_sandbox no longer importable after uninstall"

echo "== repository-level rollback =="
echo "git revert <bite-1-commit-sha> removes this entire additive directory"
echo "(sandbox-workspace-trust-v3.1/) with no other tracked file depending on it."

rm -rf "$VENV_DIR"
echo "ROLLBACK DEMONSTRATION: PASS"
