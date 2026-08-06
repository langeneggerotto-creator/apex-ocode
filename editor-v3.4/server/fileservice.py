"""Confined file operations for the editor backend: list/read/write, all bound to
a single workspace directory. Every function that touches a path resolves it and
verifies the resolution stayed inside the workspace — including through a
symlink — before doing anything, and OCode's own protected metadata directory
(``.ocode``, the same one Bite 1 hides from sandboxed processes) is invisible to
the editor too: it is not listed, not readable, not writable through this
service.
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
import tempfile
from pathlib import Path
from typing import List, Optional

PROTECTED_DIR_NAME = ".ocode"


class PathEscapeError(ValueError):
    """Raised when a requested path resolves outside the workspace, whether via
    ``..`` segments, an absolute path, or a symlink."""


class BinaryFileError(ValueError):
    """Raised when a read is requested on a file that looks binary (contains a
    null byte in its first chunk) — refused rather than mangled as UTF-8 text."""


class ConcurrencyConflictError(RuntimeError):
    """Raised when a write's ``expected_hash`` doesn't match the file's current
    on-disk content hash: the caller's copy is stale, reject rather than
    silently clobber a concurrent change."""


def _content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_safe_path(workspace: Path, rel_path: str) -> Path:
    workspace = workspace.resolve()
    if not rel_path or rel_path.startswith("/") or rel_path.startswith("\\"):
        raise PathEscapeError(f"path must be relative and non-empty: {rel_path!r}")

    candidate = (workspace / rel_path)
    # Resolve symlinks / '..' segments fully, then verify the result is still
    # inside the workspace. Path.resolve() does not require the path to exist,
    # so this also correctly rejects a not-yet-existing target under a symlinked
    # parent directory that itself points outside the workspace.
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(workspace)
    except ValueError:
        raise PathEscapeError(f"path escapes workspace: {rel_path!r} -> {resolved}") from None

    if relative.parts and relative.parts[0] == PROTECTED_DIR_NAME:
        raise PathEscapeError(f"path targets protected metadata directory: {rel_path!r}")

    return resolved


@dataclasses.dataclass(frozen=True)
class FileEntry:
    path: str
    is_dir: bool
    size: Optional[int] = None


def list_tree(workspace: Path) -> List[FileEntry]:
    workspace = workspace.resolve()
    entries: List[FileEntry] = []
    for root, dirnames, filenames in os.walk(workspace):
        dirnames[:] = [d for d in dirnames if d != PROTECTED_DIR_NAME and not d.startswith(".git")]
        root_path = Path(root)
        for d in dirnames:
            rel = (root_path / d).relative_to(workspace)
            entries.append(FileEntry(path=str(rel), is_dir=True))
        for f in filenames:
            full = root_path / f
            rel = full.relative_to(workspace)
            try:
                size = full.stat().st_size
            except OSError:
                size = None
            entries.append(FileEntry(path=str(rel), is_dir=False, size=size))
    entries.sort(key=lambda e: e.path)
    return entries


def read(workspace: Path, rel_path: str) -> "tuple[str, str]":
    path = resolve_safe_path(workspace, rel_path)
    if not path.is_file():
        raise FileNotFoundError(f"no such file: {rel_path}")

    data = path.read_bytes()
    if b"\x00" in data[:8192]:
        raise BinaryFileError(f"refusing to open as text (looks binary): {rel_path}")

    content = data.decode("utf-8", errors="replace")
    return content, _content_hash(data)


def write(workspace: Path, rel_path: str, content: str, *, expected_hash: Optional[str] = None) -> str:
    path = resolve_safe_path(workspace, rel_path)
    data = content.encode("utf-8")

    if path.exists():
        current_hash = _content_hash(path.read_bytes())
        if expected_hash is not None and expected_hash != current_hash:
            raise ConcurrencyConflictError(
                f"stale content hash for {rel_path}: expected {expected_hash}, on-disk is {current_hash}"
            )
    else:
        if expected_hash is not None:
            raise ConcurrencyConflictError(f"expected {rel_path} to exist (hash given) but it does not")
        path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to a temp file in the same directory (guarantees the
    # same filesystem, so the final rename is atomic), then os.replace() —
    # either the old content or the new content is observable, never a partial
    # write, even if this process is killed mid-write.
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    return _content_hash(data)
