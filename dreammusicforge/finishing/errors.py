"""Typed errors for the finishing package, extending core.errors'
DMFError hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class FinishingError(DMFError):
    """Raised when loudness measurement/normalization or color
    adjustment fails, or a FinishingResult fails validation. Carries
    every problem found, same discipline as every other *Error in this
    repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "finishing failed")
