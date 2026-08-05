"""Typed errors for the generation package, extending core.errors'
DMFError hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class CandidateIntakeError(DMFError):
    """Raised when a candidate can't be imported -- a missing candidate
    or reference file, or a failed validation. Carries every problem
    found, same discipline as every other *ValidationError in this
    repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "candidate intake failed")
