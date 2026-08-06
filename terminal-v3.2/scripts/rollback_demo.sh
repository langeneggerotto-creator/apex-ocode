#!/usr/bin/env bash
# Demonstrates that the Bite 2 artifact is fully removable: install into a clean
# venv (alongside its Bite 1 dependency), prove it works, uninstall just Bite 2,
# and prove the module is gone while Bite 1 remains intact and unaffected — this
# bite adds no files inside sandbox-workspace-trust-v3.1/ and modifies none of its
# behavior, so Bite 1 rolling back independently is not a concern either way.
set -euo pipefail

BITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SANDBOX_DIR="$(cd "$BITE_DIR/../sandbox-workspace-trust-v3.1" && pwd)"
VENV_DIR="$(mktemp -d)/ocode-terminal-rollback-proof"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q "$SANDBOX_DIR"
"$VENV_DIR/bin/pip" install -q "$BITE_DIR"

echo "== before rollback =="
"$VENV_DIR/bin/python3" -c "import ocode_terminal; print('present:', ocode_terminal.__file__)"
"$VENV_DIR/bin/python3" -c "import ocode_sandbox; print('bite1 present:', ocode_sandbox.__file__)"

echo "== rolling back Bite 2 only (pip uninstall) =="
"$VENV_DIR/bin/pip" uninstall -y -q ocode-terminal

echo "== after rollback =="
if "$VENV_DIR/bin/python3" -c "import ocode_terminal" 2>/dev/null; then
    echo "ROLLBACK FAILED: ocode_terminal still importable"
    exit 1
fi
echo "confirmed: ocode_terminal no longer importable after uninstall"

"$VENV_DIR/bin/python3" -c "import ocode_sandbox; print('bite1 still present, unaffected:', ocode_sandbox.__file__)"

echo "== repository-level rollback =="
echo "git revert <bite-2-commit-sha> removes this entire additive directory"
echo "(terminal-v3.2/) with no other tracked file depending on it — it adds no"
echo "files inside sandbox-workspace-trust-v3.1/ and modifies none of its behavior."

rm -rf "$VENV_DIR"
echo "ROLLBACK DEMONSTRATION: PASS"
