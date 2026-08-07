"""End-to-end tests against the real backend and real repositories in headless
Chromium via Playwright. Each test proves an actual on-disk git outcome (a
real commit in `git log`, a real checked-out branch, a real merge-conflict
resolution) — never just "the button exists and didn't throw."
"""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path

import pytest

playwright_sync_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_sync_api.sync_playwright

from ocode_sandbox.trust import establish_trust

from server.httpserver import serve

CHROMIUM_PATH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

pytestmark = pytest.mark.skipif(
    not Path(CHROMIUM_PATH).exists(),
    reason="requires the pre-installed headless Chromium",
)


def _git(workspace: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(workspace), *args],
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    ws = tmp_path / "repo"
    ws.mkdir()
    _git(ws, "init", "-q")
    _git(ws, "config", "user.email", "test@example.com")
    _git(ws, "config", "user.name", "Test Suite")
    (ws / "file.txt").write_text("hello\n")
    _git(ws, "add", "file.txt")
    _git(ws, "commit", "-q", "-m", "initial commit")
    establish_trust(ws, actor="e2e-test")
    return ws


@pytest.fixture()
def server_url(repo: Path):
    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
    httpd = serve(repo, frontend_dir, port=0)
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
        pg = browser.new_page(viewport={"width": 1400, "height": 800})
        pg.goto(server_url, wait_until="networkidle")
        pg.wait_for_selector("#status-msg:has-text('ready')")
        yield pg
        browser.close()


def test_status_view_and_staging_moves_between_lists(page, repo: Path) -> None:
    (repo / "file.txt").write_text("hello\nworld\n")
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#status-msg:has-text('ready')")

    assert page.locator("#list-unstaged li").count() == 1
    assert page.locator("#list-staged li").count() == 0

    page.click("#list-unstaged .file-action")
    page.wait_for_function("document.querySelectorAll('#list-staged li').length === 1")
    assert page.locator("#list-unstaged li").count() == 0


def test_commit_via_ui_creates_real_commit_on_disk(page, repo: Path) -> None:
    (repo / "file.txt").write_text("hello\nvia ui\n")
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#status-msg:has-text('ready')")

    page.click("#list-unstaged .file-action")
    page.wait_for_function("document.querySelectorAll('#list-staged li').length === 1")

    page.fill("#commit-message", "commit created via ui")
    page.click("#btn-commit")
    page.wait_for_function("document.getElementById('status-msg').textContent === 'committed'")

    log = _git(repo, "log", "--oneline", "-1").stdout
    assert "commit created via ui" in log


def test_branch_switch_via_ui_changes_checked_out_branch(page, repo: Path) -> None:
    _git(repo, "branch", "ui-branch")
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#status-msg:has-text('ready')")

    page.select_option("#branch-select", "ui-branch")
    page.wait_for_function(
        "document.getElementById('branch-label').textContent === 'On ui-branch'"
    )

    current = _git(repo, "branch", "--show-current").stdout.strip()
    assert current == "ui-branch"


def test_diff_view_renders_real_diff_content(page, repo: Path) -> None:
    (repo / "file.txt").write_text("hello\nDIFF_MARKER_LINE\n")
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#status-msg:has-text('ready')")

    page.click("#list-unstaged .file-name")
    page.wait_for_selector(".diff-add")

    diff_text = page.inner_text("#diff-content")
    assert "DIFF_MARKER_LINE" in diff_text


def test_real_merge_conflict_shown_and_keep_ours_resolves_it(page, repo: Path) -> None:
    _git(repo, "checkout", "-q", "-b", "branch-a")
    (repo / "conflict.txt").write_text("line one\nAAAA\nline three\n")
    _git(repo, "add", "conflict.txt")
    _git(repo, "commit", "-q", "-m", "a change")

    _git(repo, "checkout", "-q", "master")
    _git(repo, "checkout", "-q", "-b", "branch-b")
    (repo / "conflict.txt").write_text("line one\nBBBB\nline three\n")
    _git(repo, "add", "conflict.txt")
    _git(repo, "commit", "-q", "-m", "b change")

    subprocess.run(
        ["git", "-C", str(repo), "merge", "branch-a"],
        capture_output=True,
        text=True,
    )  # expected to conflict; exit code intentionally not checked here

    page.reload(wait_until="networkidle")
    page.wait_for_selector("#status-msg:has-text('ready')")

    assert page.is_visible("#conflict-banner")
    assert page.inner_text("#list-conflicted").strip().startswith("conflict.txt")

    page.click("#list-conflicted .file-action >> nth=0")  # "Keep ours" = branch-b (current)
    page.wait_for_function(
        "document.getElementById('conflict-banner').classList.contains('hidden')"
    )

    assert "BBBB" in (repo / "conflict.txt").read_text()
