#!/usr/bin/env bash
# Installs ocode_terminal (and its local monorepo dependency, ocode_sandbox) into a
# fresh, throwaway virtualenv and proves import + CLI work, independent of this
# repository checkout's working directory or PYTHONPATH.
set -euo pipefail

BITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SANDBOX_DIR="$(cd "$BITE_DIR/../sandbox-workspace-trust-v3.1" && pwd)"
VENV_DIR="$(mktemp -d)/ocode-terminal-install-proof"

echo "== creating clean venv at $VENV_DIR =="
python3 -m venv "$VENV_DIR"

echo "== installing Bite 1 dependency ($SANDBOX_DIR) into clean venv =="
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q "$SANDBOX_DIR"

echo "== installing $BITE_DIR into clean venv =="
"$VENV_DIR/bin/pip" install -q "$BITE_DIR"

echo "== import proof =="
"$VENV_DIR/bin/python3" -c "import ocode_terminal; print('import OK:', ocode_terminal.__file__)"

echo "== CLI proof =="
"$VENV_DIR/bin/python3" -m ocode_terminal --help >/dev/null
echo "CLI OK"

echo "$VENV_DIR"
