"""Backend adversarial + functional tests for the confined file service. No
browser needed — these exercise server/fileservice.py and server/httpserver.py
directly."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from ocode_sandbox.trust import establish_trust

from server import fileservice
from server.httpserver import serve


@pytest.fixture()
def trusted_workspace(tmp_path: Path) -> Path:
    establish_trust(tmp_path, actor="test-suite")
    (tmp_path / "sample.txt").write_text("hello\n")
    return tmp_path


# -- fileservice: path confinement -------------------------------------------------


def test_dotdot_path_escape_rejected(trusted_workspace: Path) -> None:
    with pytest.raises(fileservice.PathEscapeError):
        fileservice.read(trusted_workspace, "../../../etc/passwd")


def test_absolute_path_rejected(trusted_workspace: Path) -> None:
    with pytest.raises(fileservice.PathEscapeError):
        fileservice.read(trusted_workspace, "/etc/passwd")


def test_symlink_escape_rejected(trusted_workspace: Path) -> None:
    link = trusted_workspace / "escape_link"
    link.symlink_to("/etc")
    try:
        with pytest.raises(fileservice.PathEscapeError):
            fileservice.read(trusted_workspace, "escape_link/passwd")
    finally:
        link.unlink()


def test_protected_metadata_directory_blocked(trusted_workspace: Path) -> None:
    (trusted_workspace / ".ocode").mkdir(exist_ok=True)
    (trusted_workspace / ".ocode" / "trust.json").write_text("{}")
    with pytest.raises(fileservice.PathEscapeError):
        fileservice.read(trusted_workspace, ".ocode/trust.json")


def test_protected_dir_excluded_from_tree(trusted_workspace: Path) -> None:
    entries = fileservice.list_tree(trusted_workspace)
    assert not any(e.path.startswith(".ocode") for e in entries)
    assert any(e.path == "sample.txt" for e in entries)


def test_binary_file_refused(trusted_workspace: Path) -> None:
    (trusted_workspace / "bin.dat").write_bytes(b"\x00\x01\x02binary")
    with pytest.raises(fileservice.BinaryFileError):
        fileservice.read(trusted_workspace, "bin.dat")


# -- fileservice: concurrency and atomicity ----------------------------------------


def test_write_with_correct_hash_succeeds(trusted_workspace: Path) -> None:
    _, h = fileservice.read(trusted_workspace, "sample.txt")
    new_hash = fileservice.write(trusted_workspace, "sample.txt", "changed\n", expected_hash=h)
    content, h2 = fileservice.read(trusted_workspace, "sample.txt")
    assert content == "changed\n"
    assert new_hash == h2


def test_stale_hash_write_rejected_and_file_unchanged(trusted_workspace: Path) -> None:
    _, h = fileservice.read(trusted_workspace, "sample.txt")
    fileservice.write(trusted_workspace, "sample.txt", "first change\n", expected_hash=h)
    with pytest.raises(fileservice.ConcurrencyConflictError):
        fileservice.write(trusted_workspace, "sample.txt", "stale change\n", expected_hash=h)
    content, _ = fileservice.read(trusted_workspace, "sample.txt")
    assert content == "first change\n"


def test_write_new_file_creates_it(trusted_workspace: Path) -> None:
    fileservice.write(trusted_workspace, "new_dir/new_file.txt", "brand new\n")
    content, _ = fileservice.read(trusted_workspace, "new_dir/new_file.txt")
    assert content == "brand new\n"


def test_write_expecting_existing_file_that_is_missing_conflicts(trusted_workspace: Path) -> None:
    with pytest.raises(fileservice.ConcurrencyConflictError):
        fileservice.write(trusted_workspace, "does_not_exist.txt", "x", expected_hash="deadbeef")


def test_atomic_write_leaves_no_temp_file_on_success(trusted_workspace: Path) -> None:
    _, h = fileservice.read(trusted_workspace, "sample.txt")
    fileservice.write(trusted_workspace, "sample.txt", "atomic\n", expected_hash=h)
    leftover_tmp = list(trusted_workspace.glob(".*.tmp"))
    assert leftover_tmp == []


# -- httpserver: same protections, over real HTTP ----------------------------------


def _start_http(workspace: Path):
    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
    httpd = serve(workspace, frontend_dir, port=0)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    host, port = httpd.server_address
    return httpd, t, f"http://{host}:{port}"


@pytest.fixture()
def http_server(trusted_workspace: Path):
    httpd, t, base_url = _start_http(trusted_workspace)
    yield base_url, trusted_workspace
    httpd.shutdown()
    t.join(timeout=5)


def test_http_tree_and_read(http_server) -> None:
    base_url, _ = http_server
    tree = json.loads(urllib.request.urlopen(f"{base_url}/api/tree").read())
    assert any(e["path"] == "sample.txt" for e in tree)

    data = json.loads(urllib.request.urlopen(f"{base_url}/api/file?path=sample.txt").read())
    assert data["content"] == "hello\n"


def test_http_write_round_trip(http_server) -> None:
    base_url, _ = http_server
    data = json.loads(urllib.request.urlopen(f"{base_url}/api/file?path=sample.txt").read())
    body = json.dumps({"content": "via http\n", "expected_hash": data["hash"]}).encode()
    req = urllib.request.Request(f"{base_url}/api/file?path=sample.txt", data=body, method="PUT")
    result = json.loads(urllib.request.urlopen(req).read())
    assert "hash" in result

    reread = json.loads(urllib.request.urlopen(f"{base_url}/api/file?path=sample.txt").read())
    assert reread["content"] == "via http\n"


def test_http_path_escape_rejected_with_403(http_server) -> None:
    base_url, _ = http_server
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(f"{base_url}/api/file?path=../../etc/passwd")
    assert exc_info.value.code == 403


def test_http_conflict_returns_409(http_server) -> None:
    base_url, _ = http_server
    body = json.dumps({"content": "conflict\n", "expected_hash": "not-the-real-hash"}).encode()
    req = urllib.request.Request(f"{base_url}/api/file?path=sample.txt", data=body, method="PUT")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 409


def test_http_untrusted_workspace_refused_everywhere(tmp_path: Path) -> None:
    httpd, t, base_url = _start_http(tmp_path)  # no establish_trust() called
    try:
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"{base_url}/api/tree")
        assert exc_info.value.code == 403

        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"{base_url}/")
        assert exc_info.value.code == 403
    finally:
        httpd.shutdown()
        t.join(timeout=5)
