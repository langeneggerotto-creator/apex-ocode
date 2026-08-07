#!/usr/bin/env bash
# Runs the full Bite 5 gate: spec gate, clean-environment install proof,
# backend + Playwright end-to-end tests, a representative screenshot, and a
# rollback proof - then writes a single evidence manifest capturing exact
# commands and outcomes.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SANDBOX_DIR="$REPO_ROOT/sandbox-workspace-trust-v3.1"
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

echo "== 3/4 test suite (backend + Playwright e2e) =="
TEST_LOG="$EVIDENCE_DIR/.test_log.txt"
JUNIT_XML="$EVIDENCE_DIR/.junit.xml"
(
    cd "$BITE_DIR"
    PYTHONPATH="$SANDBOX_DIR/src" python3 -m pytest tests/ -v --junitxml="$JUNIT_XML"
) | tee "$TEST_LOG"
TEST_EXIT=${PIPESTATUS[0]}

echo "== capturing a representative screenshot as visual evidence =="
SCREENSHOT_WS="$(mktemp -d)/ocode-git-workspace-evidence-ws"
mkdir -p "$SCREENSHOT_WS"
git -C "$SCREENSHOT_WS" init -q
git -C "$SCREENSHOT_WS" config user.email evidence@example.com
git -C "$SCREENSHOT_WS" config user.name "Evidence Capture"
cat > "$SCREENSHOT_WS/app.py" <<'PYEOF'
def greet(name):
    return f"hello, {name}"
PYEOF
git -C "$SCREENSHOT_WS" add app.py
git -C "$SCREENSHOT_WS" commit -q -m "initial commit"
PYTHONPATH="$SANDBOX_DIR/src" python3 -m ocode_sandbox trust "$SCREENSHOT_WS" --actor evidence-capture >/dev/null
(
    cd "$BITE_DIR"
    PYTHONPATH="$SANDBOX_DIR/src" python3 - "$SCREENSHOT_WS" <<'PYEOF'
import subprocess
import sys, threading, time
sys.path.insert(0, ".")
from pathlib import Path
from server.httpserver import serve
from playwright.sync_api import sync_playwright

workspace = Path(sys.argv[1])
(workspace / "app.py").write_text(
    "def greet(name):\n"
    "    return f\"hello, {name}\"\n"
    "\n\nprint(greet(\"world\"))\n"
)

httpd = serve(workspace, Path("frontend"), port=0)
host, port = httpd.server_address
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
time.sleep(0.3)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto(f"http://{host}:{port}", wait_until="networkidle")
    page.wait_for_selector("#status-msg:has-text('ready')")
    page.click("#list-unstaged .file-name")
    page.wait_for_selector(".diff-add")
    page.screenshot(path="evidence/screenshot.png")
    browser.close()

httpd.shutdown()
print("screenshot captured: evidence/screenshot.png")
PYEOF
)
SCREENSHOT_EXIT=$?

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
echo "screenshot exit:     $SCREENSHOT_EXIT"
echo "rollback proof exit: $ROLLBACK_EXIT"

if [ "$GATE_EXIT" -ne 0 ] || [ "$INSTALL_EXIT" -ne 0 ] || [ "$TEST_EXIT" -ne 0 ] || [ "$ROLLBACK_EXIT" -ne 0 ] || [ "$MANIFEST_EXIT" -ne 0 ]; then
    echo "BITE 5 GATES: FAIL"
    exit 1
fi
echo "BITE 5 GATES: PASS"
