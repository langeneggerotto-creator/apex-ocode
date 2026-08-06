"""JobClient: a plain Python wrapper around the daemon's Unix-socket protocol."""

from __future__ import annotations

import base64
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


class JobServiceUnavailableError(RuntimeError):
    """Raised when the daemon's socket cannot be connected to."""


class JobClient:
    def __init__(self, socket_path: Path):
        self.socket_path = Path(socket_path)

    def _request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        from .protocol import MessageStream

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(str(self.socket_path))
        except OSError as exc:
            raise JobServiceUnavailableError(f"cannot connect to job daemon at {self.socket_path}: {exc}") from exc
        stream = MessageStream(sock)
        try:
            stream.send(message)
            reply = stream.recv()
            if reply is None:
                raise JobServiceUnavailableError("connection closed before a reply arrived")
            return reply
        finally:
            stream.close()

    def submit(
        self,
        command: Sequence[str],
        *,
        task_name: Optional[str] = None,
        timeout_seconds: int = 600,
        limits: Optional[Dict[str, int]] = None,
    ) -> str:
        reply = self._request(
            {
                "type": "submit",
                "command": list(command),
                "task_name": task_name,
                "timeout_seconds": timeout_seconds,
                "limits": limits,
            }
        )
        return reply["job_id"]

    def status(self, job_id: str) -> Dict[str, Any]:
        reply = self._request({"type": "status", "job_id": job_id})
        if reply.get("type") == "error":
            raise KeyError(reply.get("message"))
        return reply["job"]

    def list(self) -> List[Dict[str, Any]]:
        reply = self._request({"type": "list"})
        return reply["jobs"]

    def cancel(self, job_id: str) -> bool:
        reply = self._request({"type": "cancel", "job_id": job_id})
        return bool(reply.get("ok"))

    def logs(self, job_id: str) -> bytes:
        reply = self._request({"type": "logs", "job_id": job_id})
        if reply.get("type") == "error":
            raise KeyError(reply.get("message"))
        return base64.b64decode(reply["data"])

    def shutdown(self) -> None:
        self._request({"type": "shutdown"})
