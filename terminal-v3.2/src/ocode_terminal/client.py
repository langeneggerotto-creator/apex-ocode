"""TerminalClient: a plain Python wrapper around the daemon's Unix-socket protocol.

One connection == one attach/detach cycle. Requests that get an immediate reply
(``resize``, ``stop``, ``status``) and asynchronous pushes (``output``, ``exited``)
share the same stream, so callers that need both read messages in a loop and switch
on ``type`` — the same pattern the CLI's interactive attach loop uses.
"""

from __future__ import annotations

import collections
import socket
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, Optional

from .protocol import MessageStream, decode_bytes, encode_bytes


class SessionUnavailableError(RuntimeError):
    """Raised when the daemon's socket cannot be connected to — the session is
    gone (crashed, host rebooted, never started) rather than merely busy."""


class TerminalClient:
    """One connection == one attach/detach cycle.

    The daemon can push ``output``/``exited`` messages at any time, independent of
    whatever request/reply is in flight, so a reply to e.g. ``resize`` can be
    preceded on the wire by an unrelated ``output`` push. ``_await_reply`` filters
    for the expected reply type(s) and queues anything else it skips past, so
    ``read_message`` (used by callers that want to observe the live output stream)
    never silently loses a message that a control call happened to skip over.
    """

    def __init__(self, socket_path: Path):
        self.socket_path = Path(socket_path)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(str(self.socket_path))
        except OSError as exc:
            raise SessionUnavailableError(f"cannot connect to session at {self.socket_path}: {exc}") from exc
        self._stream = MessageStream(sock)
        self._pending: Deque[Dict[str, Any]] = collections.deque()

    def _await_reply(self, expected_types: Iterable[str]) -> Dict[str, Any]:
        """Read raw messages directly off the wire (bypassing ``_pending``) until one
        matches. Must NOT go through ``_pending`` on the read side: queueing a
        skipped message there and then re-checking ``_pending`` first on the next
        loop iteration would immediately hand back the very message just queued,
        looping on it forever instead of reading the next one off the socket.
        """
        expected = set(expected_types)
        while True:
            msg = self._stream.recv()
            if msg is None:
                raise SessionUnavailableError("connection closed while awaiting reply")
            if msg.get("type") in expected:
                return msg
            self._pending.append(msg)
            # A pending message we just skipped past is exactly what read_message()
            # is for; move on rather than blocking forever on a type that may never
            # arrive because, e.g., the session already exited.
            if msg.get("type") == "exited" and "exited" not in expected:
                return msg

    def attach(self) -> bytes:
        self._stream.send({"type": "attach"})
        msg = self._await_reply({"scrollback"})
        return decode_bytes(msg.get("data", ""))

    def send_input(self, data: bytes) -> None:
        self._stream.send({"type": "input", "data": encode_bytes(data)})

    def resize(self, cols: int, rows: int) -> Dict[str, Any]:
        self._stream.send({"type": "resize", "cols": cols, "rows": rows})
        return self._await_reply({"status", "error", "exited"})

    def status(self) -> Dict[str, Any]:
        self._stream.send({"type": "status"})
        return self._await_reply({"status", "error", "exited"})

    def stop(self, force: bool = False) -> Dict[str, Any]:
        self._stream.send({"type": "stop", "force": force})
        return self._await_reply({"status", "error", "exited"})

    def detach(self) -> None:
        try:
            self._stream.send({"type": "detach"})
        except OSError:
            pass
        self._stream.close()

    def read_message(self) -> Optional[Dict[str, Any]]:
        if self._pending:
            return self._pending.popleft()
        return self._stream.recv()

    def close(self) -> None:
        self._stream.close()
