"""Minimal stdlib-only local HTTP server: serves the static graphical git
frontend and a JSON API mirroring every :mod:`gitservice` operation, gated on
Bite 1's workspace trust check (reused unmodified — this server never
establishes trust itself, only verifies it). Binds to localhost only; this is
a local-mode, single-user tool, not a network-exposed service
(`SECURITY_DEPLOYMENT.md`).
"""

from __future__ import annotations

import dataclasses
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ocode_sandbox.trust import verify_trust

from . import gitservice as gs
from .gitservice import (
    GitOperationError,
    InvalidRefError,
    PathEscapeError,
    WorkspaceNotTrustedError,
)

# Errors this API layer knows how to turn into a clean 4xx JSON response
# rather than a 500 — every other exception is a bug and is allowed to
# surface as a 500 so it isn't silently mistaken for expected user input.
_CLIENT_ERRORS = (PathEscapeError, InvalidRefError, GitOperationError, WorkspaceNotTrustedError)


def _status_for(exc: Exception) -> int:
    if isinstance(exc, WorkspaceNotTrustedError):
        return 403
    if isinstance(exc, PathEscapeError):
        return 403
    if isinstance(exc, InvalidRefError):
        return 400
    if isinstance(exc, GitOperationError):
        return 409
    return 500


def _json_bytes(obj) -> bytes:
    return json.dumps(obj).encode("utf-8")


def _truthy(value) -> bool:
    return str(value).lower() in ("1", "true", "yes")


def make_handler(workspace: Path, frontend_dir: Path):
    workspace = workspace.resolve()
    frontend_dir = frontend_dir.resolve()

    class Handler(BaseHTTPRequestHandler):
        server_version = "OCodeGitWorkspace/0.1"

        def log_message(self, fmt, *args):  # noqa: A003 - stdlib signature
            pass  # quiet; evidence capture reads structured logs, not stdout noise

        def _send_json(self, status: int, obj) -> None:
            body = _json_bytes(obj)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            try:
                return json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return {}

        def _require_trust(self) -> bool:
            if verify_trust(workspace) is None:
                self._send_json(403, {"error": "workspace is not trusted (no valid trust marker)"})
                return False
            return True

        def _serve_static(self, url_path: str) -> None:
            rel = url_path.lstrip("/") or "index.html"
            candidate = (frontend_dir / rel).resolve()
            try:
                candidate.relative_to(frontend_dir)
            except ValueError:
                self.send_error(403, "forbidden")
                return
            if candidate.is_dir():
                candidate = candidate / "index.html"
            if not candidate.is_file():
                self.send_error(404, "not found")
                return
            data = candidate.read_bytes()
            content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _dispatch(self, method: str, parsed, body: dict) -> bool:
            """Handles one /api/git/* route. Returns True if it matched (whether
            or not it succeeded) so callers can fall through to static/404."""
            path = parsed.path
            qs = parse_qs(parsed.query)

            def qs1(key: str, default: str = "") -> str:
                return (qs.get(key) or [default])[0]

            try:
                if method == "GET" and path == "/api/git/status":
                    self._send_json(200, dataclasses.asdict(gs.status(workspace)))
                elif method == "GET" and path == "/api/git/diff":
                    p = qs1("path") or None
                    text = gs.diff(workspace, p, staged=_truthy(qs1("staged")))
                    self._send_json(200, {"diff": text})
                elif method == "GET" and path == "/api/git/log":
                    limit = int(qs1("limit", "50") or "50")
                    self._send_json(200, [dataclasses.asdict(c) for c in gs.log(workspace, limit)])
                elif method == "GET" and path == "/api/git/branches":
                    self._send_json(200, [dataclasses.asdict(b) for b in gs.branches(workspace)])
                elif method == "GET" and path == "/api/git/tags":
                    self._send_json(200, {"tags": gs.tags(workspace)})
                elif method == "GET" and path == "/api/git/stash":
                    self._send_json(200, {"stash": gs.stash_list(workspace)})
                elif method == "GET" and path == "/api/git/conflicts":
                    self._send_json(200, {"conflicts": gs.conflicted_files(workspace)})
                elif method == "POST" and path == "/api/git/stage":
                    gs.stage(workspace, body.get("paths", []))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/unstage":
                    gs.unstage(workspace, body.get("paths", []))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/commit":
                    sha = gs.commit(workspace, body.get("message", ""))
                    self._send_json(200, {"sha": sha})
                elif method == "POST" and path == "/api/git/branch":
                    gs.create_branch(workspace, body.get("name", ""))
                    self._send_json(200, {"ok": True})
                elif method == "DELETE" and path == "/api/git/branch":
                    gs.delete_branch(workspace, qs1("name"))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/switch":
                    gs.switch_branch(workspace, body.get("name", ""))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/tag":
                    gs.create_tag(workspace, body.get("name", ""))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/stash/save":
                    gs.stash_save(workspace, body.get("message") or None)
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/stash/pop":
                    gs.stash_pop(workspace, int(body.get("index", 0)))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/stash/drop":
                    gs.stash_drop(workspace, int(body.get("index", 0)))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/restore":
                    gs.restore(workspace, body.get("path", ""))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/cherry-pick":
                    gs.cherry_pick(workspace, body.get("sha", ""))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/cherry-pick/abort":
                    gs.cherry_pick_abort(workspace)
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/rebase":
                    gs.rebase(workspace, body.get("onto", ""))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/rebase/abort":
                    gs.rebase_abort(workspace)
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/merge":
                    gs.merge(workspace, body.get("branch", ""))
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/merge/abort":
                    gs.merge_abort(workspace)
                    self._send_json(200, {"ok": True})
                elif method == "POST" and path == "/api/git/resolve":
                    gs.resolve(workspace, body.get("path", ""), body.get("strategy", ""))
                    self._send_json(200, {"ok": True})
                else:
                    return False
            except _CLIENT_ERRORS as exc:
                self._send_json(_status_for(exc), {"error": str(exc)})
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
            return True

        def do_GET(self) -> None:  # noqa: N802 - stdlib method name
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/"):
                if not self._require_trust():
                    return
                if self._dispatch("GET", parsed, {}):
                    return
                self.send_error(404, "not found")
                return
            self._serve_static(parsed.path)

        def do_POST(self) -> None:  # noqa: N802 - stdlib method name
            parsed = urlparse(self.path)
            if not self._require_trust():
                return
            body = self._read_json_body()
            if self._dispatch("POST", parsed, body):
                return
            self.send_error(404, "not found")

        def do_DELETE(self) -> None:  # noqa: N802 - stdlib method name
            parsed = urlparse(self.path)
            if not self._require_trust():
                return
            if self._dispatch("DELETE", parsed, {}):
                return
            self.send_error(404, "not found")

    return Handler


def serve(workspace: Path, frontend_dir: Path, *, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    handler = make_handler(workspace, frontend_dir)
    httpd = ThreadingHTTPServer((host, port), handler)
    return httpd
