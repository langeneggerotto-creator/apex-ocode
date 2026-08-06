"""Newline-delimited JSON message framing shared by the daemon and client.

Deliberately a small, closed set of message types rather than raw byte forwarding —
this is the "mobile-safe controls" contract: a client can only attach, send input,
resize, detach, stop, or ask for status. There is no message type that lets a client
do anything outside that bounded surface.
"""

from __future__ import annotations

import base64
import json
import socket
import threading
from typing import Any, Dict, Optional

MAX_LINE_BYTES = 1024 * 1024  # 1 MiB cap per framed message (mobile-safe bound)

CLIENT_MESSAGE_TYPES = {"attach", "input", "resize", "detach", "stop", "status"}
SERVER_MESSAGE_TYPES = {"scrollback", "output", "exited", "status", "error"}


def encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def decode_bytes(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


class MessageStream:
    """Buffered newline-delimited JSON reader/writer over a connected socket.

    ``send`` is guarded by a lock: the daemon has one thread reading/broadcasting
    (``output``/``exited`` pushes) and another handling a given client's requests
    (``status``/``resize``/``stop`` replies), and both can call ``send`` on the same
    connection concurrently. Without serializing, two unsynchronized ``sendall``
    calls on the same socket can interleave their underlying writes and corrupt the
    newline-delimited framing.
    """

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
