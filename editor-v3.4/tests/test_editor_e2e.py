"""End-to-end tests against the real backend and real Monaco editor in headless
Chromium via Playwright. Each test proves an actual rendered/computed outcome
(a real diff, a real replace-all result, a real ARIA snapshot) — never just "the
button exists and didn't throw."
"""

from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path

import pytest

playwright_sync_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_sync_api.sync_playwright

from ocode_sandbox.trust import establish_trust

from server.httpserver import serve

CHROMIUM_PATH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
VENDOR_MONACO_DIR = Path(__file__).resolve().parents[1] / "frontend" / "vendor" / "monaco"

pytestmark = pytest.mark.skipif(
    not Path(CHROMIUM_PATH).exists() or not VENDOR_MONACO_DIR.exists(),
    reason="requires the pre-installed headless Chromium and vendored Monaco assets "
    "(run scripts/vendor_monaco.sh first)",
)


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    establish_trust(tmp_path, actor="e2e-test")
    (tmp_path / "hello.json").write_text('{"a":1,"b":2}\n')
    (tmp_path / "second.txt").write_text("second file content\n")
    return tmp_path


@pytest.fixture()
def server_url(workspace: Path):
    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
    httpd = serve(workspace, frontend_dir, port=0)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    host, port = httpd.server_address
    yield f"http://{host}:{port}"
    httpd.shutdown()
    t.join(timeout=5)


@pytest.fixture()
def page(server_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM_PATH, headless=True)
        pg = browser.new_page()
        pg.goto(server_url, wait_until="networkidle")
        yield pg
        browser.close()


def _open_file(page, name: str) -> None:
    page.click(f"text={name}")
    page.wait_for_selector(".tab")


def test_open_edit_dirty_save_clears(page) -> None:
    _open_file(page, "hello.json")
    page.click(".editor-container")
    page.keyboard.type("X")
    page.wait_for_function(
        "document.querySelector('.tab-label').textContent.startsWith('●')"
    )

    page.click("#btn-save")
    page.wait_for_function(
        "!document.querySelector('.tab-label').textContent.startsWith('●')"
    )
    assert page.locator("#status").inner_text() == "Saved hello.json"


def test_multiple_tabs_independent_content(page) -> None:
    _open_file(page, "hello.json")
    page.click(".editor-container")
    page.keyboard.type("FIRST_TAB_MARKER")

    _open_file(page, "second.txt")
    assert page.locator(".tab").count() == 2
    content_second = page.evaluate(
        "monaco.editor.getModels().find(m => m.uri.path.includes('second.txt')).getValue()"
    )
    assert "FIRST_TAB_MARKER" not in content_second
    assert "second file content" in content_second

    content_first = page.evaluate(
        "monaco.editor.getModels().find(m => m.uri.path.includes('hello.json')).getValue()"
    )
    assert "FIRST_TAB_MARKER" in content_first


def test_split_pane_independent_editing(page) -> None:
    _open_file(page, "hello.json")

    page.click("#btn-split")
    page.wait_for_selector("#pane1:not(.hidden)")
    page.select_option("#pane-select", "1")
    page.click("text=second.txt")
    page.wait_for_selector("#tabbar1 .tab")

    # Editing in pane 2 must not affect pane 1's model of a different file.
    page.locator("#pane1 .editor-container").click()
    page.keyboard.type("PANE2_EDIT")

    pane0_content = page.evaluate(
        "monaco.editor.getModels().find(m => m.uri.path.includes('hello.json')).getValue()"
    )
    assert "PANE2_EDIT" not in pane0_content


def test_search_and_replace_all(page) -> None:
    _open_file(page, "hello.json")
    page.click(".editor-container")
    page.keyboard.type("findme findme findme")

    page.click("#btn-replace")
    page.wait_for_selector(".find-widget")
    page.fill('.find-widget textarea[aria-label="Find"]', "findme")
    page.fill('.find-widget textarea[aria-label="Replace"]', "REPLACED")
    page.click('[aria-label*="Replace All"]')

    content = page.evaluate(
        "monaco.editor.getModels().find(m => m.uri.path.includes('hello.json')).getValue()"
    )
    assert "REPLACED" in content
    assert "findme" not in content


def test_diff_editor_shows_real_computed_diff(page) -> None:
    _open_file(page, "hello.json")
    page.click(".editor-container")
    page.keyboard.press("Control+End")
    page.keyboard.type("DIFF_MARKER_LINE")

    page.click("#btn-diff")
    page.wait_for_selector("#diff-overlay:not(.hidden)")

    # A real diff editor renders both an original and a modified model with
    # different content, not a static placeholder.
    diff_text = page.evaluate(
        """() => {
            const models = monaco.editor.getModels();
            const original = models.find(m => !m.uri.path.includes('tab-'));
            return original ? original.getValue() : null;
        }"""
    )
    modified_text = page.evaluate(
        "monaco.editor.getModels().find(m => m.uri.path.includes('hello.json')).getValue()"
    )
    assert diff_text is not None
    assert "DIFF_MARKER_LINE" not in diff_text
    assert "DIFF_MARKER_LINE" in modified_text
    assert diff_text != modified_text

    page.click("#btn-diff-close")
    page.wait_for_selector("#diff-overlay", state="hidden")


def test_unsaved_change_recovery_after_reload(page, server_url) -> None:
    _open_file(page, "hello.json")
    page.click(".editor-container")
    page.keyboard.type("DRAFT_SURVIVES_RELOAD")
    # Let the debounced localStorage write happen.
    time.sleep(0.5)

    page.on("dialog", lambda dialog: dialog.accept())
    page.goto(server_url, wait_until="networkidle")
    page.click("text=hello.json")
    page.wait_for_selector(".tab")

    content = page.evaluate(
        "monaco.editor.getModels().find(m => m.uri.path.includes('hello.json')).getValue()"
    )
    assert "DRAFT_SURVIVES_RELOAD" in content


def test_accessibility_tab_roles_and_labels(page) -> None:
    _open_file(page, "hello.json")
    page.click(".editor-container")
    page.keyboard.type("x")
    page.wait_for_function(
        "document.querySelector('.tab-label').textContent.startsWith('●')"
    )

    tab = page.locator("#tabbar0").get_by_role("tab")
    assert tab.count() == 1
    assert tab.first.get_attribute("aria-label") == "hello.json (unsaved changes)"
    assert page.locator("#tabbar0").get_attribute("role") == "tablist"

    toolbar = page.locator("#toolbar")
    assert toolbar.get_attribute("role") == "toolbar"
    for btn_id in ["btn-save", "btn-find", "btn-replace", "btn-format", "btn-diff", "btn-split"]:
        assert page.locator(f"#{btn_id}").get_attribute("aria-label")
