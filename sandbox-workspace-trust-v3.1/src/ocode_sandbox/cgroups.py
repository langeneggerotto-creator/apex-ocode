"""Cgroup-enforced resource limits for sandboxed runs.

Supports cgroup v1 legacy hierarchies (``/sys/fs/cgroup/<controller>``) and cgroup v2
unified hierarchies (``/sys/fs/cgroup/unified`` or a single ``/sys/fs/cgroup`` mount
with ``cgroup2`` type), whichever is actually writable on the host. If neither is
usable, the sandbox refuses to run unconfined: resource limiting is a mandatory
control, not a best-effort one.
"""

from __future__ import annotations

import dataclasses
import os
import time
import uuid
from pathlib import Path
from typing import Optional


class CgroupUnavailableError(RuntimeError):
    """Raised when no writable cgroup controller can be found. Fail closed: callers
    must not fall back to running without resource limits."""


@dataclasses.dataclass(frozen=True)
class ResourceLimits:
    memory_bytes: int = 256 * 1024 * 1024
    pids_max: int = 128
    cpu_quota_percent: Optional[int] = 100  # None disables CPU throttling


_V1_ROOTS = {
    "memory": Path("/sys/fs/cgroup/memory"),
    "pids": Path("/sys/fs/cgroup/pids"),
    "cpu": Path("/sys/fs/cgroup/cpu"),
}

_V2_CANDIDATES = [Path("/sys/fs/cgroup/unified"), Path("/sys/fs/cgroup")]


def _v1_controller_writable(controller: str) -> bool:
    root = _V1_ROOTS[controller]
    return root.is_dir() and os.access(root, os.W_OK)


def _v2_root() -> Optional[Path]:
    for candidate in _V2_CANDIDATES:
        controllers_file = candidate / "cgroup.controllers"
        subtree_file = candidate / "cgroup.subtree_control"
        if controllers_file.is_file() and subtree_file.is_file():
            try:
                enabled = subtree_file.read_text().split()
            except OSError:
                continue
            if {"memory", "pids"}.issubset(enabled) and os.access(candidate, os.W_OK):
                return candidate
    return None


class CgroupSandbox:
    """Context manager that creates a per-run cgroup, applies limits, and removes the
    cgroup on exit. Prefers cgroup v1 legacy (validated as functional in the reference
    development environment); falls back to cgroup v2 unified if v1 is not writable
    but v2 delegates the required controllers.
    """

    def __init__(self, limits: ResourceLimits, name: Optional[str] = None):
        self.limits = limits
        self.name = name or f"ocode-sandbox-{uuid.uuid4().hex[:12]}"
        self._mode: Optional[str] = None
        self._v1_paths: dict[str, Path] = {}
        self._v2_path: Optional[Path] = None

    @property
    def mode(self) -> Optional[str]:
        return self._mode

    def __enter__(self) -> "CgroupSandbox":
        if _v1_controller_writable("memory") and _v1_controller_writable("pids"):
            self._mode = "v1"
            for controller in ("memory", "pids", "cpu"):
                root = _V1_ROOTS[controller]
                if not root.is_dir() or not os.access(root, os.W_OK):
                    continue
                path = root / self.name
                path.mkdir(parents=True, exist_ok=True)
                self._v1_paths[controller] = path

            (self._v1_paths["memory"] / "memory.limit_in_bytes").write_text(str(self.limits.memory_bytes))
            (self._v1_paths["pids"] / "pids.max").write_text(str(self.limits.pids_max))
            if "cpu" in self._v1_paths and self.limits.cpu_quota_percent is not None:
                period = 100_000
                quota = int(period * self.limits.cpu_quota_percent / 100)
                (self._v1_paths["cpu"] / "cpu.cfs_period_us").write_text(str(period))
                (self._v1_paths["cpu"] / "cpu.cfs_quota_us").write_text(str(quota))
            return self

        v2_root = _v2_root()
        if v2_root is not None:
            self._mode = "v2"
            path = v2_root / self.name
            path.mkdir(parents=True, exist_ok=True)
            (path / "memory.max").write_text(str(self.limits.memory_bytes))
            (path / "pids.max").write_text(str(self.limits.pids_max))
            if self.limits.cpu_quota_percent is not None:
                period = 100_000
                quota = int(period * self.limits.cpu_quota_percent / 100)
                (path / "cpu.max").write_text(f"{quota} {period}")
            self._v2_path = path
            return self

        raise CgroupUnavailableError(
            "no writable cgroup v1 (memory+pids) or cgroup v2 (memory+pids delegated) "
            "controller found; refusing to start an unconfined sandbox"
        )

    def procs_paths(self) -> list[Path]:
        """Path(s) to write a PID into to join this cgroup. Callers that need the
        limited process to self-assign (recommended — see fs_isolation.py for why an
        external, post-hoc assignment races against ``unshare --fork``) should embed
        an ``echo $$ > <path>`` for each entry into the sandboxed process's own
        startup script rather than calling add_pid() from outside after Popen."""
        if self._mode == "v1":
            return [path / "cgroup.procs" for path in self._v1_paths.values()]
        if self._mode == "v2" and self._v2_path is not None:
            return [self._v2_path / "cgroup.procs"]
        return []

    def add_pid(self, pid: int) -> None:
        if self._mode == "v1":
            for path in self._v1_paths.values():
                (path / "cgroup.procs").write_text(str(pid))
        elif self._mode == "v2" and self._v2_path is not None:
            (self._v2_path / "cgroup.procs").write_text(str(pid))
        else:
            raise CgroupUnavailableError("cgroup not entered")

    def usage(self) -> dict:
        if self._mode == "v1":
            mem_path = self._v1_paths.get("memory")
            pids_path = self._v1_paths.get("pids")
            return {
                "mode": "v1",
                "memory_max_usage_bytes": _read_int(mem_path / "memory.max_usage_in_bytes") if mem_path else None,
                "memory_failcnt": _read_int(mem_path / "memory.failcnt") if mem_path else None,
                "pids_current": _read_int(pids_path / "pids.current") if pids_path else None,
            }
        if self._mode == "v2" and self._v2_path is not None:
            return {
                "mode": "v2",
                "memory_current_bytes": _read_int(self._v2_path / "memory.current"),
                "pids_current": _read_int(self._v2_path / "pids.current"),
            }
        return {"mode": None}

    def __exit__(self, exc_type, exc, tb) -> None:
        paths = list(self._v1_paths.values()) if self._mode == "v1" else (
            [self._v2_path] if self._v2_path else []
        )
        for path in paths:
            _rmdir_retry(path)


def _read_int(path: Path) -> Optional[int]:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def _rmdir_retry(path: Path, attempts: int = 20, delay_seconds: float = 0.1) -> None:
    for _ in range(attempts):
        try:
            path.rmdir()
            return
        except FileNotFoundError:
            return
        except OSError:
            time.sleep(delay_seconds)
    # Leaving a residual empty cgroup directory is a non-fatal cleanup miss; it does
    # not grant any additional privilege and will be reclaimed on next process exit.
