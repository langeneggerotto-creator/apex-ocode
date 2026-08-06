#!/usr/bin/env bash
# Installs ocode_sandbox into a fresh, throwaway virtualenv and proves import + CLI
# work, independent of this repository checkout's working directory or PYTHONPATH.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$(mktemp -d)/ocode-sandbox-install-proof"

echo "== creating clean venv at $VENV_DIR =="
python3 -m venv "$VENV_DIR"

echo "== installing $REPO_DIR into clean venv =="
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q "$REPO_DIR"

echo "== import proof =="
"$VENV_DIR/bin/python3" -c "import ocode_sandbox; print('import OK:', ocode_sandbox.__file__)"

echo "== CLI proof =="
"$VENV_DIR/bin/python3" -m ocode_sandbox --help >/dev/null
echo "CLI OK"

echo "$VENV_DIR"
