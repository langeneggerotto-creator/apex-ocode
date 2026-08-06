"""OCode Bite 2 — Persistent, sandboxed, reconnectable integrated terminal (local mode)."""

from .client import SessionUnavailableError, TerminalClient
from .session import (
    ChildDiscoveryError,
    SandboxSetupError,
    SpawnedSession,
    StopResult,
    WorkspaceNotTrustedError,
)

__all__ = [
    "TerminalClient",
    "SessionUnavailableError",
    "SpawnedSession",
    "StopResult",
    "WorkspaceNotTrustedError",
    "SandboxSetupError",
    "ChildDiscoveryError",
]
