#!/usr/bin/env bash
# Proves this bite's "install" story from a clean state: copy the bite into a
# scratch directory (simulating a fresh clone), install Bite 1's dependency
# into a fresh venv, and prove the backend server starts and serves both the
# static frontend and the git JSON API against a trusted real git repo. No
# npm/vendoring step is needed here — the frontend is plain JS, unlike Bite
# 4's vendored Monaco.
set -euo pipefail

BITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SANDBOX_DIR="$(cd "$BITE_DIR/../sandbox-workspace-trust-v3.1" && pwd)"
SCRATCH_DIR="$(mktemp -d)/ocode-git-workspace-install-proof"

echo "== copying bite into scratch dir (simulating a fresh clone) =="
mkdir -p "$SCRATCH_DIR"
cp -r "$BITE_DIR"/. "$SCRATCH_DIR"/
rm -rf "$SCRATCH_DIR/.pytest_cache"

echo "== creating clean venv and installing Bite 1 dependency =="
VENV_DIR="$(mktemp -d)/ocode-git-workspace-venv"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q "$SANDBOX_DIR"

echo "== proving the backend server starts, serves the UI, and drives real git =="
WORKSPACE_DIR="$(mktemp -d)/ocode-git-workspace-install-repo"
mkdir -p "$WORKSPACE_DIR"
git -C "$WORKSPACE_DIR" init -q
git -C "$WORKSPACE_DIR" config user.email install-proof@example.com
git -C "$WORKSPACE_DIR" config user.name "Install Proof"
echo '{"proof": true}' > "$WORKSPACE_DIR/proof.json"
git -C "$WORKSPACE_DIR" add proof.json
git -C "$WORKSPACE_DIR" commit -q -m "install proof initial commit"
PYTHONPATH="$SANDBOX_DIR/src" "$VENV_DIR/bin/python3" -m ocode_sandbox trust "$WORKSPACE_DIR" --actor install-proof >/dev/null

cd "$SCRATCH_DIR"
PYTHONPATH="$SANDBOX_DIR/src" "$VENV_DIR/bin/python3" -c "
import sys, threading, time, json, urllib.request
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
assert b'OCode Source Control' in index, 'index.html did not serve correctly'
status = json.loads(urllib.request.urlopen(base + '/api/git/status').read())
assert status == {'staged': [], 'unstaged': [], 'untracked': [], 'conflicted': []}, status
log = json.loads(urllib.request.urlopen(base + '/api/git/log').read())
assert log[0]['subject'] == 'install proof initial commit', log
httpd.shutdown()
print('backend serve + real git proof: OK')
"

echo "$SCRATCH_DIR"
echo "$VENV_DIR"
