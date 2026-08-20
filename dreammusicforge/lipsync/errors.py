"""Typed errors for the lipsync package, extending core.errors' DMFError
hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class LipSyncError(DMFError):
    """Raised when a LipSyncRequest/LipSyncResult fails validation, or
    when a request is built for a shot that doesn't need lip sync.
    Carries every problem found, same discipline as every other
    *Error in this repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "lip-sync validation failed")
