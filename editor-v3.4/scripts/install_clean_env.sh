#!/usr/bin/env bash
# Proves this bite's "install" story from a clean state: copy the bite into a
# scratch directory (simulating a fresh clone that hasn't vendored Monaco yet),
# vendor Monaco via npm, and prove the backend server starts and serves both the
# static frontend and the JSON API against a trusted workspace.
set -euo pipefail

BITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SANDBOX_DIR="$(cd "$BITE_DIR/../sandbox-workspace-trust-v3.1" && pwd)"
SCRATCH_DIR="$(mktemp -d)/ocode-editor-install-proof"

echo "== copying bite into scratch dir (simulating a fresh clone) =="
mkdir -p "$SCRATCH_DIR"
cp -r "$BITE_DIR"/. "$SCRATCH_DIR"/
rm -rf "$SCRATCH_DIR/frontend/vendor" "$SCRATCH_DIR/npm-install-scratch" "$SCRATCH_DIR/.pytest_cache"

echo "== creating clean venv and installing Bite 1 dependency =="
VENV_DIR="$(mktemp -d)/ocode-editor-venv"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q "$SANDBOX_DIR"

echo "== vendoring Monaco from npm (no runtime CDN dependency) =="
bash "$SCRATCH_DIR/scripts/vendor_monaco.sh"

echo "== proving the backend server starts and serves the app =="
WORKSPACE_DIR="$(mktemp -d)/ocode-editor-install-workspace"
mkdir -p "$WORKSPACE_DIR"
echo '{"proof": true}' > "$WORKSPACE_DIR/proof.json"
PYTHONPATH="$SANDBOX_DIR/src" "$VENV_DIR/bin/python3" -m ocode_sandbox trust "$WORKSPACE_DIR" --actor install-proof >/dev/null

cd "$SCRATCH_DIR"
PYTHONPATH="$SANDBOX_DIR/src" "$VENV_DIR/bin/python3" -c "
import sys, threading, time, urllib.request
sys.path.insert(0, '.')
from pathlib import Path
from server.httpserver import serve

httpd = serve(Path('$WORKSPACE_DIR'), Path('frontend'), port=0)
host, port = httpd.server_address
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
time.sleep(0.3)
base = f'http://{host}:{port}'
index = urllib.request.urlopen(base + '/').read()
assert b'OCode Editor' in index, 'index.html did not serve correctly'
tree = urllib.request.urlopen(base + '/api/tree').read()
assert b'proof.json' in tree, 'API did not see the workspace file'
httpd.shutdown()
print('backend serve proof: OK')
"

echo "$SCRATCH_DIR"
echo "$VENV_DIR"
