"""create_operator_server(): a minimal, dependency-free HTTP server
(stdlib `http.server` only, no new dependency) that serves one
pre-rendered OperatorReport snapshot at `GET /`.

This is a real, functioning server -- not a mock -- but it serves a
fixed snapshot rendered once at creation time; it does not re-query any
store on each request, because no persistence layer exists anywhere in
this codebase yet (see models.py's module docstring). Rebuilding the
report and creating a new server (or a future release adding a
`refresh()` method backed by real storage) is how a caller gets a
newer snapshot.

The caller owns the server's lifecycle: call `serve_forever()` (usually
in a background thread) and `shutdown()` when done, or call
`handle_request()` once to serve exactly one request, same pattern
`http.server.HTTPServer` always uses.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer

from .models import OperatorReport
from .render import render_report_html


def _make_handler(html_bytes: bytes) -> type[BaseHTTPRequestHandler]:
    class OperatorReportHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (stdlib method name)
            if self.path != "/":
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)

        def log_message(self, format: str, *args) -> None:  # noqa: A002 (stdlib signature)
            pass  # silence default stderr access logging -- this is a local operator tool, not a production service

    return OperatorReportHandler


def create_operator_server(report: OperatorReport, host: str = "127.0.0.1", port: int = 0) -> HTTPServer:
    html_bytes = render_report_html(report).encode("utf-8")
    handler = _make_handler(html_bytes)
    return HTTPServer((host, port), handler)
