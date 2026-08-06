"""Newline-delimited JSON message framing for the job manager daemon/client.

Deliberately the same small, closed-message-type pattern as Bite 2's protocol
(duplicated rather than imported: this bite does not depend on ``ocode_terminal`` —
jobs are batch/non-interactive, they have no PTY, and depending on a PTY-specific
package just to reuse ~50 lines of generic framing would be the wrong kind of
coupling). Any future bite that wants a shared transport library can factor this
out explicitly; duplicating it here keeps each bite's dependency footprint minimal
and its own concern.
"""

from __future__ import annotations

import json
import socket
import threading
from typing import Any, Dict, Optional

MAX_LINE_BYTES = 1024 * 1024


class MessageStream:
    """Buffered newline-delimited JSON reader/writer over a connected socket.
    ``send`` is guarded by a lock since the daemon can have multiple threads
    writing to the same client connection concurrently (see Bite 2's daemon for
    the concurrency pattern this mirrors)."""

    def __init__(self, sock: socket.socket):
        self._sock = sock
        self._buffer = b""
        self._send_lock = threading.Lock()

    def send(self, message: Dict[str, Any]) -> None:
        line = json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\n"
        if len(line) > MAX_LINE_BYTES:
            raise ValueError("message exceeds MAX_LINE_BYTES")
        with self._send_lock:
            self._sock.sendall(line)

    def recv(self) -> Optional[Dict[str, Any]]:
        while b"\n" not in self._buffer:
            if len(self._buffer) > MAX_LINE_BYTES:
                raise ValueError("incoming message exceeds MAX_LINE_BYTES")
            chunk = self._sock.recv(65536)
            if not chunk:
                return None
            self._buffer += chunk
        line, self._buffer = self._buffer.split(b"\n", 1)
        if not line:
            return {}
        return json.loads(line.decode("utf-8"))

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass
