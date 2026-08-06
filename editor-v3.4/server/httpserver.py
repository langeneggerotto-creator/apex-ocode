"""Minimal stdlib-only local HTTP server: serves the static Monaco frontend and a
small JSON file-service API, both gated on Bite 1's workspace trust check
(reused unmodified — this server never establishes trust itself, only verifies
it). Binds to localhost only; this is a local-mode, single-user tool, not a
network-exposed service (`SECURITY_DEPLOYMENT.md`).
"""

from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ocode_sandbox.trust import verify_trust

from . import fileservice
from .fileservice import BinaryFileError, ConcurrencyConflictError, PathEscapeError


def _json_bytes(obj) -> bytes:
    return json.dumps(obj).encode("utf-8")


def make_handler(workspace: Path, frontend_dir: Path):
    workspace = workspace.resolve()
    frontend_dir = frontend_dir.resolve()

    class Handler(BaseHTTPRequestHandler):
        server_version = "OCodeEditor/0.1"

        def log_message(self, fmt, *args):  # noqa: A003 - stdlib signature
            pass  # quiet; evidence capture reads structured logs, not stdout noise

        def _send_json(self, status: int, obj) -> None:
            body = _json_bytes(obj)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

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

        def do_GET(self) -> None:  # noqa: N802 - stdlib method name
            parsed = urlparse(self.path)
            if not self._require_trust():
                return

            if parsed.path == "/api/tree":
                entries = fileservice.list_tree(workspace)
                self._send_json(200, [dataclasses_asdict(e) for e in entries])
                return

            if parsed.path == "/api/file":
                qs = parse_qs(parsed.query)
                rel_path = (qs.get("path") or [""])[0]
                try:
                    content, content_hash = fileservice.read(workspace, rel_path)
                except PathEscapeError as exc:
                    self._send_json(403, {"error": str(exc)})
                except BinaryFileError as exc:
                    self._send_json(415, {"error": str(exc)})
                except FileNotFoundError as exc:
                    self._send_json(404, {"error": str(exc)})
                else:
                    self._send_json(200, {"content": content, "hash": content_hash})
                return

            self._serve_static(parsed.path)

        def do_PUT(self) -> None:  # noqa: N802 - stdlib method name
            parsed = urlparse(self.path)
            if not self._require_trust():
                return

            if parsed.path != "/api/file":
                self.send_error(404, "not found")
                return

            qs = parse_qs(parsed.query)
            rel_path = (qs.get("path") or [""])[0]
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._send_json(400, {"error": "invalid JSON body"})
                return

            content = payload.get("content", "")
            expected_hash = payload.get("expected_hash")
            try:
                new_hash = fileservice.write(workspace, rel_path, content, expected_hash=expected_hash)
            except PathEscapeError as exc:
                self._send_json(403, {"error": str(exc)})
            except ConcurrencyConflictError as exc:
                self._send_json(409, {"error": str(exc)})
            else:
                self._send_json(200, {"hash": new_hash})

    return Handler


def dataclasses_asdict(entry: fileservice.FileEntry) -> dict:
    return {"path": entry.path, "is_dir": entry.is_dir, "size": entry.size}


def serve(workspace: Path, frontend_dir: Path, *, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    handler = make_handler(workspace, frontend_dir)
    httpd = ThreadingHTTPServer((host, port), handler)
    return httpd
