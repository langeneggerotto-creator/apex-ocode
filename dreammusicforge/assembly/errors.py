"""Typed errors for the assembly package, extending core.errors'
DMFError hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class AssemblyError(DMFError):
    """Raised when assembly fails -- a rejected or mismatched candidate,
    a missing file, an ffmpeg failure, or a failed validation. Carries
    every problem found, same discipline as every other
    *ValidationError in this repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "assembly failed")
