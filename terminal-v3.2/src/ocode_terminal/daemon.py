"""SessionDaemon: owns a sandboxed PTY session, a scrollback ring buffer, a capped
input-event history, an idle/max-duration watchdog, and a Unix domain socket server
implementing the bounded attach/input/resize/detach/stop/status protocol.

Runs as its own OS process (see _daemon_main.py) so a session survives the CLI
invocation that started it — this is what makes "reconnect" a real, testable
capability instead of an in-process simulation.
"""

from __future__ import annotations

import collections
import json
import os
import socket
import threading
import time
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Sequence

from ocode_sandbox.cgroups import ResourceLimits
from ocode_sandbox.evidence import scrub

from . import session as session_mod
from .protocol import MessageStream, decode_bytes, encode_bytes

SCROLLBACK_CAP_BYTES = 1 * 1024 * 1024
HISTORY_CAP_ENTRIES = 500
DEFAULT_IDLE_TIMEOUT_SECONDS = 15 * 60
DEFAULT_MAX_DURATION_SECONDS = 8 * 60 * 60
WATCHDOG_INTERVAL_SECONDS = 1.0


class SessionDaemon:
    def __init__(
        self,
        workspace_dir: Path,
        command: Sequence[str],
        socket_path: Path,
        *,
        run_id: str,
        evidence_dir: Optional[Path] = None,
        limits: Optional[ResourceLimits] = None,
        cols: int = session_mod.DEFAULT_COLS,
        rows: int = session_mod.DEFAULT_ROWS,
        idle_timeout_seconds: float = DEFAULT_IDLE_TIMEOUT_SECONDS,
        max_duration_seconds: float = DEFAULT_MAX_DURATION_SECONDS,
        grace_seconds: float = 5.0,
    ):
        self.workspace_dir = Path(workspace_dir)
        self.command = list(command)
        self.socket_path = Path(socket_path)
        self.run_id = run_id
        self.evidence_dir = Path(evidence_dir) if evidence_dir else None
        self.limits = limits
        self.idle_timeout_seconds = idle_timeout_seconds
        self.max_duration_seconds = max_duration_seconds
        self.grace_seconds = grace_seconds

        self._spawned: Optional[session_mod.SpawnedSession] = None
        self._scrollback = bytearray()
        self._scrollback_lock = threading.Lock()
        self._history: Deque[Dict[str, Any]] = collections.deque(maxlen=HISTORY_CAP_ENTRIES)
        self._resize_events: List[Dict[str, Any]] = []
        self._clients: List[MessageStream] = []
        self._clients_lock = threading.Lock()

        self._started_at = time.time()
        self._last_activity = self._started_at
        self._output_bytes = 0
        self._input_bytes = 0
        self._exit_code: Optional[int] = None
        self._stop_reason: Optional[str] = None
        self._escalated = False
        self._shutdown_event = threading.Event()
        self._cols = cols
        self._rows = rows

    # -- lifecycle ---------------------------------------------------------

    def run(self) -> int:
        self._spawned = session_mod.spawn(
            self.workspace_dir,
            self.command,
            run_id=self.run_id,
            limits=self.limits,
            cols=self._cols,
            rows=self._rows,
        )

        reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        reader_thread.start()
        watchdog_thread.start()

        self._serve_socket()

        reader_thread.join(timeout=10)
        watchdog_thread.join(timeout=10)
        self._write_evidence()
        self._cleanup_socket()
        return 0

    def _reader_loop(self) -> None:
        assert self._spawned is not None
        fd = self._spawned.master_fd
        while not self._shutdown_event.is_set():
            try:
                chunk = os.read(fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            self._last_activity = time.time()
            self._output_bytes += len(chunk)
            with self._scrollback_lock:
                self._scrollback.extend(chunk)
                overflow = len(self._scrollback) - SCROLLBACK_CAP_BYTES
                if overflow > 0:
                    del self._scrollback[:overflow]
            self._broadcast({"type": "output", "data": encode_bytes(chunk)})

        if self._stop_reason is None:
            self._stop_reason = "process_exited"
        self._reap()
        self._broadcast({"type": "exited", "exit_code": self._exit_code, "escalated": self._escalated})
        self._shutdown_event.set()

    def _watchdog_loop(self) -> None:
        while not self._shutdown_event.wait(WATCHDOG_INTERVAL_SECONDS):
            now = time.time()
            if now - self._last_activity > self.idle_timeout_seconds:
                self._stop_reason = "idle_timeout"
                self._request_stop(force=False)
                break
            if now - self._started_at > self.max_duration_seconds:
                self._stop_reason = "max_duration_timeout"
                self._request_stop(force=False)
                break

    def _request_stop(self, *, force: bool) -> None:
        """Signal the process only. Deliberately does not wait/reap/clean up the
        cgroup — ``_reap`` (called from ``_reader_loop`` once it observes real EOF)
        is the sole place that does that, so there is exactly one authority for
        "the process is gone" instead of two threads racing to report it."""
        if self._spawned is None or self._spawned.outer_proc.returncode is not None:
            return
        # Set self._escalated from the on_escalate callback (fires synchronously at
        # the moment SIGKILL is sent), not from signal_stop's return value: the
        # reader thread races to detect the process's death independently via PTY
        # EOF and broadcasts using self._escalated's current value the moment it
        # notices — using the return value here (only available after death is
        # *confirmed*) can lose that race and broadcast a stale False.
        session_mod.signal_stop(
            self._spawned,
            grace_seconds=self.grace_seconds,
            force=force,
            on_escalate=lambda: setattr(self, "_escalated", True),
        )

    def _reap(self) -> None:
        if self._spawned is None:
            return
        proc = self._spawned.outer_proc
        if proc.returncode is None:
            try:
                proc.wait(timeout=self.grace_seconds + 10)
            except Exception:
                pass
        self._exit_code = proc.returncode
        try:
            self._spawned.cgroup.__exit__(None, None, None)
        except Exception:
            pass

    # -- socket server -------------------------------------------------------

    def _serve_socket(self) -> None:
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(self.socket_path))
        os.chmod(self.socket_path, 0o600)
        srv.listen(8)
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

    def _handle_client(self, conn: socket.socket) -> None:
        stream = MessageStream(conn)
        attached = False
        try:
            while True:
                msg = stream.recv()
                if msg is None:
                    break
                msg_type = msg.get("type")

                if msg_type == "attach":
                    with self._scrollback_lock:
                        snapshot = bytes(self._scrollback)
                    stream.send({"type": "scrollback", "data": encode_bytes(snapshot)})
                    with self._clients_lock:
                        self._clients.append(stream)
                    attached = True

                elif msg_type == "input":
                    data = decode_bytes(msg.get("data", ""))
                    self._last_activity = time.time()
                    self._input_bytes += len(data)
                    self._history.append(
                        {
                            "ts": time.time(),
                            "byte_len": len(data),
                            "text_scrubbed": scrub(data.decode("utf-8", errors="replace"))[:500],
                        }
                    )
                    if self._spawned is not None:
                        os.write(self._spawned.master_fd, data)

                elif msg_type == "resize":
                    cols, rows = int(msg.get("cols", self._cols)), int(msg.get("rows", self._rows))
                    if self._spawned is not None:
                        session_mod.set_winsize(self._spawned.master_fd, cols, rows)
                    self._cols, self._rows = cols, rows
                    self._resize_events.append({"ts": time.time(), "cols": cols, "rows": rows})
                    stream.send({"type": "status", **self._status_dict()})

                elif msg_type == "detach":
                    break

                elif msg_type == "stop":
                    self._stop_reason = "client_request"
                    self._request_stop(force=bool(msg.get("force", False)))
                    # Wait for the reader thread to observe the actual exit (it sets
                    # shutdown_event itself once _reap() completes) so this reply's
                    # exit_code/running fields are the final, authoritative values
                    # rather than a snapshot racing the reader thread's own finish.
                    self._shutdown_event.wait(timeout=self.grace_seconds + 15)
                    stream.send({"type": "status", **self._status_dict()})

                elif msg_type == "status":
                    stream.send({"type": "status", **self._status_dict()})

                else:
                    stream.send({"type": "error", "message": f"unknown message type: {msg_type}"})
        except (OSError, ValueError):
            pass
        finally:
            if attached:
                with self._clients_lock:
                    if stream in self._clients:
                        self._clients.remove(stream)
            stream.close()

    def _broadcast(self, message: Dict[str, Any]) -> None:
        with self._clients_lock:
            clients = list(self._clients)
        for c in clients:
            try:
                c.send(message)
            except OSError:
                with self._clients_lock:
                    if c in self._clients:
                        self._clients.remove(c)

    def _status_dict(self) -> Dict[str, Any]:
        running = self._spawned is not None and self._spawned.outer_proc.returncode is None
        return {
            "run_id": self.run_id,
            "running": running,
            "cols": self._cols,
            "rows": self._rows,
            "output_bytes": self._output_bytes,
            "input_bytes": self._input_bytes,
            "started_at": self._started_at,
            "exit_code": self._exit_code,
        }

    def _cleanup_socket(self) -> None:
        try:
            if self.socket_path.exists():
                self.socket_path.unlink()
        except OSError:
            pass

    def _write_evidence(self) -> None:
        if self.evidence_dir is None:
            return
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "schema_version": "ocode.terminal-session-evidence.v1",
            "run_id": self.run_id,
            "workspace": str(self.workspace_dir),
            "command": [scrub(part) for part in self.command],
            "controls_applied": self._spawned.controls_applied if self._spawned else None,
            "started_at": self._started_at,
            "finished_at": time.time(),
            "stop_reason": self._stop_reason,
            "escalated": self._escalated,
            "exit_code": self._exit_code,
            "output_bytes": self._output_bytes,
            "input_bytes": self._input_bytes,
            "resize_events": self._resize_events,
            "input_history": list(self._history),
        }
        out_path = self.evidence_dir / f"terminal-session-{self.run_id}.json"
        out_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
