"""Declarative task manifest: ``.ocode/tasks.json`` in the workspace.

Fails closed on malformed manifests — a task definition with a missing command, an
unknown type, or a non-list command raises rather than being silently skipped or
coerced, since a silently-dropped task could later be assumed to exist by a caller.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

MANIFEST_RELATIVE_PATH = ".ocode/tasks.json"

VALID_TASK_TYPES = {
    "run",
    "test",
    "lint",
    "format",
    "type-check",
    "build",
    "preview",
    "migration",
}

DEFAULT_TIMEOUT_SECONDS = 600


class ManifestError(ValueError):
    """Raised for any malformed manifest — fail closed, never guess."""


@dataclasses.dataclass(frozen=True)
class TaskSpec:
    name: str
    type: str
    command: List[str]
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    memory_bytes: Optional[int] = None
    pids_max: Optional[int] = None
    cpu_quota_percent: Optional[int] = None


@dataclasses.dataclass(frozen=True)
class TaskManifest:
    tasks: Dict[str, TaskSpec]

    def get(self, name: str) -> TaskSpec:
        try:
            return self.tasks[name]
        except KeyError:
            raise ManifestError(f"no such task: {name!r} (known: {sorted(self.tasks)})") from None


def _parse_task(name: str, raw: Any) -> TaskSpec:
    if not isinstance(raw, dict):
        raise ManifestError(f"task {name!r}: definition must be an object")

    task_type = raw.get("type")
    if task_type not in VALID_TASK_TYPES:
        raise ManifestError(f"task {name!r}: type must be one of {sorted(VALID_TASK_TYPES)}, got {task_type!r}")

    command = raw.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(c, str) for c in command):
        raise ManifestError(f"task {name!r}: command must be a non-empty list of strings")

    timeout_seconds = raw.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ManifestError(f"task {name!r}: timeout_seconds must be a positive number")

    for field in ("memory_bytes", "pids_max", "cpu_quota_percent"):
        if field in raw and not isinstance(raw[field], int):
            raise ManifestError(f"task {name!r}: {field} must be an integer")

    return TaskSpec(
        name=name,
        type=task_type,
        command=list(command),
        timeout_seconds=int(timeout_seconds),
        memory_bytes=raw.get("memory_bytes"),
        pids_max=raw.get("pids_max"),
        cpu_quota_percent=raw.get("cpu_quota_percent"),
    )


def parse(text: str) -> TaskManifest:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON: {exc}") from exc

    if not isinstance(data, dict) or "tasks" not in data:
        raise ManifestError("manifest must be an object with a top-level 'tasks' key")

    raw_tasks = data["tasks"]
    if not isinstance(raw_tasks, dict):
        raise ManifestError("'tasks' must be an object mapping task name to definition")

    tasks = {name: _parse_task(name, raw) for name, raw in raw_tasks.items()}
    return TaskManifest(tasks=tasks)


def load(workspace: Path) -> TaskManifest:
    path = Path(workspace) / MANIFEST_RELATIVE_PATH
    if not path.is_file():
        raise ManifestError(f"no task manifest at {path}")
    return parse(path.read_text(encoding="utf-8"))
