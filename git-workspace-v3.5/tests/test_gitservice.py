"""Backend adversarial + functional tests for the hardened git service. Every
test operates on a real git repository this suite creates and tears down —
no mocking of subprocess or git itself, per CLAUDE.md's "no capability
without executable evidence."
"""

from __future__ import annotations

import json
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from ocode_sandbox.trust import establish_trust

from server import gitservice as gs
from server.httpserver import serve


def _git(workspace: Path, *args: str) -> subprocess.CompletedProcess:
    """Raw git, bypassing the module under test — used only to set up fixture
    state (so tests aren't circularly validating gitservice using itself)."""
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
    establish_trust(ws, actor="test-suite")
    return ws


# -- hardening: 1-3 -----------------------------------------------------------


def test_hooks_are_disabled(repo: Path) -> None:
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    marker = repo / "HOOK_RAN"
    hook = hooks_dir / "pre-commit"
    hook.write_text(f"#!/bin/sh\ntouch {marker}\n")
    hook.chmod(0o755)

    (repo / "file.txt").write_text("hello\nchanged\n")
    gs.stage(repo, ["file.txt"])
    gs.commit(repo, "should not run the hook")

    assert not marker.exists()


def test_external_diff_is_disabled(repo: Path) -> None:
    marker = repo / "EXTDIFF_RAN"
    fake_diff = repo / "fake-difftool.sh"
    fake_diff.write_text(f"#!/bin/sh\ntouch {marker}\nexit 0\n")
    fake_diff.chmod(0o755)
    _git(repo, "config", "diff.external", str(fake_diff))

    (repo / "file.txt").write_text("hello\nchanged\n")
    text = gs.diff(repo, "file.txt")

    assert not marker.exists()
    assert "+changed" in text


def test_no_hang_on_blocking_pager(repo: Path) -> None:
    _git(repo, "config", "core.pager", "cat -; while true; do sleep 1; done")
    # Should return promptly; gitservice always forces core.pager=cat itself.
    commits = gs.log(repo)
    assert len(commits) == 1


# -- functional round trips: 4-9 ----------------------------------------------


def test_status_stage_unstage_commit_round_trip(repo: Path) -> None:
    (repo / "file.txt").write_text("hello\nworld\n")
    (repo / "untracked.txt").write_text("new\n")

    status = gs.status(repo)
    assert status.unstaged == ["file.txt"]
    assert status.untracked == ["untracked.txt"]
    assert status.staged == []

    gs.stage(repo, ["file.txt", "untracked.txt"])
    status = gs.status(repo)
    assert set(status.staged) == {"file.txt", "untracked.txt"}
    assert status.unstaged == []
    assert status.untracked == []

    gs.unstage(repo, ["untracked.txt"])
    status = gs.status(repo)
    assert status.staged == ["file.txt"]
    assert status.untracked == ["untracked.txt"]

    sha = gs.commit(repo, "add world line")
    assert len(sha) == 40
    log = gs.log(repo)
    assert log[0].sha == sha
    assert log[0].subject == "add world line"


def test_diff_shows_expected_content(repo: Path) -> None:
    (repo / "file.txt").write_text("hello\nworld\n")
    text = gs.diff(repo, "file.txt")
    assert "+world" in text
    assert "-hello" not in text  # unchanged context line, not removed


def test_branch_lifecycle(repo: Path) -> None:
    gs.create_branch(repo, "feature")
    names = {b.name for b in gs.branches(repo)}
    assert "feature" in names

    gs.switch_branch(repo, "feature")
    assert gs.current_branch(repo) == "feature"

    with pytest.raises(gs.GitOperationError):
        gs.delete_branch(repo, "feature")  # refuses to delete current branch

    gs.switch_branch(repo, "master")
    gs.delete_branch(repo, "feature")
    assert "feature" not in {b.name for b in gs.branches(repo)}


def test_tag_create_and_list(repo: Path) -> None:
    gs.create_tag(repo, "v1.0.0")
    assert gs.tags(repo) == ["v1.0.0"]


def test_stash_round_trip(repo: Path) -> None:
    (repo / "file.txt").write_text("hello\nstashed change\n")
    gs.stash_save(repo, "wip")
    assert (repo / "file.txt").read_text() == "hello\n"  # reverted by stash
    assert len(gs.stash_list(repo)) == 1

    gs.stash_pop(repo)
    assert (repo / "file.txt").read_text() == "hello\nstashed change\n"
    assert gs.stash_list(repo) == []


def test_restore_discards_only_targeted_path(repo: Path) -> None:
    (repo / "file.txt").write_text("hello\nchanged\n")
    (repo / "other.txt").write_text("other content\n")
    gs.stage(repo, ["other.txt"])

    gs.restore(repo, "file.txt")

    assert (repo / "file.txt").read_text() == "hello\n"
    assert gs.status(repo).staged == ["other.txt"]  # untouched


# -- cherry-pick, rebase, merge conflict: 10-12 --------------------------------


def test_cherry_pick_applies_commit_onto_another_branch(repo: Path) -> None:
    gs.create_branch(repo, "feature")
    gs.switch_branch(repo, "feature")
    (repo / "feature.txt").write_text("feature content\n")
    gs.stage(repo, ["feature.txt"])
    sha = gs.commit(repo, "add feature file")

    gs.switch_branch(repo, "master")
    assert not (repo / "feature.txt").exists()

    gs.cherry_pick(repo, sha)
    assert (repo / "feature.txt").read_text() == "feature content\n"
    assert gs.log(repo)[0].subject == "add feature file"


def test_rebase_fast_forwardable(repo: Path) -> None:
    gs.create_branch(repo, "topic")
    gs.switch_branch(repo, "topic")
    (repo / "topic.txt").write_text("topic content\n")
    gs.stage(repo, ["topic.txt"])
    gs.commit(repo, "topic commit")

    gs.switch_branch(repo, "master")
    (repo / "master_only.txt").write_text("master only\n")
    gs.stage(repo, ["master_only.txt"])
    gs.commit(repo, "master-only commit")

    gs.switch_branch(repo, "topic")
    gs.rebase(repo, "master")

    subjects = [c.subject for c in gs.log(repo)]
    assert subjects[:2] == ["topic commit", "master-only commit"]
    assert (repo / "master_only.txt").exists()


def test_merge_conflict_list_and_resolve_ours_and_theirs(repo: Path) -> None:
    gs.create_branch(repo, "branch-a")
    gs.create_branch(repo, "branch-b")

    gs.switch_branch(repo, "branch-a")
    (repo / "conflict.txt").write_text("line one\nAAAA\nline three\n")
    gs.stage(repo, ["conflict.txt"])
    gs.commit(repo, "a change")

    gs.switch_branch(repo, "branch-b")
    (repo / "conflict.txt").write_text("line one\nBBBB\nline three\n")
    gs.stage(repo, ["conflict.txt"])
    gs.commit(repo, "b change")

    with pytest.raises(gs.GitOperationError):
        gs.merge(repo, "branch-a")

    assert gs.conflicted_files(repo) == ["conflict.txt"]

    # "ours" = current branch (branch-b) at merge time.
    gs.resolve(repo, "conflict.txt", "ours")
    assert "BBBB" in (repo / "conflict.txt").read_text()
    assert gs.conflicted_files(repo) == []
    gs.commit(repo, "resolve with ours")

    # Redo the same conflict and resolve with "theirs" this time.
    gs.switch_branch(repo, "branch-b")
    _git(repo, "reset", "-q", "--hard", "HEAD~1")
    with pytest.raises(gs.GitOperationError):
        gs.merge(repo, "branch-a")
    gs.resolve(repo, "conflict.txt", "theirs")
    assert "AAAA" in (repo / "conflict.txt").read_text()
    assert gs.conflicted_files(repo) == []


def test_merge_abort_clears_conflict_state(repo: Path) -> None:
    gs.create_branch(repo, "branch-a")
    gs.create_branch(repo, "branch-b")

    gs.switch_branch(repo, "branch-a")
    (repo / "conflict.txt").write_text("AAAA\n")
    gs.stage(repo, ["conflict.txt"])
    gs.commit(repo, "a change")

    gs.switch_branch(repo, "branch-b")
    (repo / "conflict.txt").write_text("BBBB\n")
    gs.stage(repo, ["conflict.txt"])
    gs.commit(repo, "b change")

    with pytest.raises(gs.GitOperationError):
        gs.merge(repo, "branch-a")
    assert gs.conflicted_files(repo) == ["conflict.txt"]

    gs.merge_abort(repo)
    assert gs.conflicted_files(repo) == []
    assert gs.status(repo) == gs.GitStatus(staged=[], unstaged=[], untracked=[], conflicted=[])


# -- fail-closed / confinement: 13-14 ------------------------------------------


def test_untrusted_workspace_refuses_before_spawning_git(tmp_path: Path) -> None:
    ws = tmp_path / "untrusted"
    ws.mkdir()
    _git(ws, "init", "-q")
    # deliberately no establish_trust()
    with pytest.raises(gs.WorkspaceNotTrustedError):
        gs.status(ws)


def test_path_escape_rejected(repo: Path) -> None:
    with pytest.raises(gs.PathEscapeError):
        gs.stage(repo, ["../../etc/passwd"])
    with pytest.raises(gs.PathEscapeError):
        gs.diff(repo, "../../etc/passwd")


def test_symlink_escape_rejected(repo: Path) -> None:
    link = repo / "escape_link"
    link.symlink_to("/etc")
    try:
        with pytest.raises(gs.PathEscapeError):
            gs.stage(repo, ["escape_link/passwd"])
    finally:
        link.unlink()


def test_protected_metadata_directory_hidden_and_blocked(repo: Path) -> None:
    status = gs.status(repo)
    assert not any(p.startswith(".ocode") for p in status.untracked)

    with pytest.raises(gs.PathEscapeError):
        gs.stage(repo, [".ocode/trust.json"])
    with pytest.raises(gs.PathEscapeError):
        gs.restore(repo, ".ocode/trust.json")


def test_invalid_ref_rejected_before_spawning_git() -> None:
    with pytest.raises(gs.InvalidRefError):
        gs.validate_ref("-evil-flag")
    with pytest.raises(gs.InvalidRefError):
        gs.validate_ref("")
    with pytest.raises(gs.InvalidRefError):
        gs.validate_sha("not-a-sha; rm -rf /")


def test_git_operation_error_surfaces_stdout_when_stderr_empty(repo: Path) -> None:
    # git's "nothing to commit"-family messages go to stdout, not stderr; the
    # error message must not be silently empty just because git chose that
    # stream (the .ocode dir being untracked-but-hidden means this repo's
    # exact wording is "nothing added to commit", not "working tree clean" —
    # either way it must not be the empty string).
    with pytest.raises(gs.GitOperationError) as exc_info:
        gs.commit(repo, "nothing changed")
    message = str(exc_info.value).lower()
    assert "nothing" in message and "commit" in message


# -- httpserver: same operations and protections, over real HTTP --------------


def _start_http(workspace: Path):
    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
    httpd = serve(workspace, frontend_dir, port=0)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    host, port = httpd.server_address
    return httpd, t, f"http://{host}:{port}"


@pytest.fixture()
def http_server(repo: Path):
    httpd, t, base_url = _start_http(repo)
    yield base_url, repo
    httpd.shutdown()
    t.join(timeout=5)


def _req(base_url: str, method: str, path: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        base_url + path, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_http_status_stage_commit_round_trip(http_server) -> None:
    base_url, ws = http_server
    (ws / "file.txt").write_text("hello\nvia http\n")

    status_code, body = _req(base_url, "GET", "/api/git/status")
    assert status_code == 200
    assert body["unstaged"] == ["file.txt"]

    status_code, _ = _req(base_url, "POST", "/api/git/stage", {"paths": ["file.txt"]})
    assert status_code == 200

    status_code, body = _req(base_url, "POST", "/api/git/commit", {"message": "via http"})
    assert status_code == 200
    assert len(body["sha"]) == 40


def test_http_bad_ref_returns_400(http_server) -> None:
    base_url, _ = http_server
    status_code, body = _req(base_url, "POST", "/api/git/branch", {"name": "-evil"})
    assert status_code == 400
    assert "error" in body


def test_http_path_escape_returns_403(http_server) -> None:
    base_url, _ = http_server
    status_code, body = _req(base_url, "GET", "/api/git/diff?path=../../etc/passwd")
    assert status_code == 403


def test_http_protected_dir_returns_403(http_server) -> None:
    base_url, _ = http_server
    status_code, body = _req(base_url, "POST", "/api/git/stage", {"paths": [".ocode/trust.json"]})
    assert status_code == 403


def test_http_untrusted_workspace_refused(tmp_path: Path) -> None:
    ws = tmp_path / "untrusted"
    ws.mkdir()
    _git(ws, "init", "-q")
    httpd, t, base_url = _start_http(ws)
    try:
        status_code, _ = _req(base_url, "GET", "/api/git/status")
        assert status_code == 403
    finally:
        httpd.shutdown()
        t.join(timeout=5)
