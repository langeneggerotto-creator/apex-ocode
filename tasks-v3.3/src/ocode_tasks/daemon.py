"""JobDaemon: serves a JobManager over a Unix domain socket so job submission,
status, cancellation, and logs work across separate CLI invocations — the same
persistence rationale as Bite 2's terminal daemon, adapted for a job queue that
(unlike a single PTY session) manages many jobs over its lifetime and stays up
until explicitly told to stop.
"""

from __future__ import annotations

import base64
import os
import socket
import threading
from pathlib import Path
from typing import List, Optional

from ocode_sandbox.cgroups import ResourceLimits

from .manager import JobManager
from .protocol import MessageStream


class JobDaemon:
    def __init__(
        self,
        workspace: Path,
        socket_path: Path,
        *,
        concurrency: int = 2,
        evidence_dir: Optional[Path] = None,
    ):
        self.workspace = Path(workspace)
        self.socket_path = Path(socket_path)
        self.manager = JobManager(workspace, concurrency=concurrency, evidence_dir=evidence_dir)
        self._shutdown_event = threading.Event()

    def run(self) -> int:
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(self.socket_path))
        os.chmod(self.socket_path, 0o600)
        srv.listen(16)
        srv.settimeout(0.5)

        threads: List[threading.Thread] = []
        while not self._shutdown_event.is_set():
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
            t.start()
            threads.append(t)

        srv.close()
        for t in threads:
            t.join(timeout=2)

        self.manager.shutdown()
        try:
            if self.socket_path.exists():
                self.socket_path.unlink()
        except OSError:
            pass
        return 0

    def _handle_client(self, conn: socket.socket) -> None:
        stream = MessageStream(conn)
        try:
            while True:
                msg = stream.recv()
                if msg is None:
                    break
                msg_type = msg.get("type")

                if msg_type == "submit":
                    limits = None
                    if msg.get("limits"):
                        limits = ResourceLimits(**msg["limits"])
                    job_id = self.manager.submit(
                        msg["command"],
                        task_name=msg.get("task_name"),
                        timeout_seconds=msg.get("timeout_seconds", 600),
                        limits=limits,
                    )
                    stream.send({"type": "submitted", "job_id": job_id})

                elif msg_type == "status":
                    job = self.manager.status(msg.get("job_id", ""))
                    if job is None:
                        stream.send({"type": "error", "message": "no such job"})
                    else:
                        stream.send({"type": "status", "job": job.to_dict()})

                elif msg_type == "list":
                    stream.send({"type": "list", "jobs": [j.to_dict() for j in self.manager.list()]})

                elif msg_type == "cancel":
                    ok = self.manager.cancel(msg.get("job_id", ""))
                    stream.send({"type": "cancelled", "ok": ok})

                elif msg_type == "logs":
                    data = self.manager.logs(msg.get("job_id", ""))
                    if data is None:
                        stream.send({"type": "error", "message": "no such job"})
                    else:
                        stream.send({"type": "logs", "data": base64.b64encode(data).decode("ascii")})

                elif msg_type == "shutdown":
                    stream.send({"type": "shutting_down"})
                    self._shutdown_event.set()
                    break

                else:
                    stream.send({"type": "error", "message": f"unknown message type: {msg_type}"})
        except (OSError, ValueError):
            pass
        finally:
            stream.close()
