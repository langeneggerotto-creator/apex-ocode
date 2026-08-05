"""Storage layer -- Release 0.1 ships one backend (SQLite, per spec
section 13.1's development baseline). Later releases add the
production-ready design in section 13.2 behind the same ProjectRepository
interface shape."""
from __future__ import annotations

from .sqlite_repository import ProjectRepository

__all__ = ["ProjectRepository"]
