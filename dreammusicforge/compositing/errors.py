"""Typed errors for the compositing package, extending core.errors'
DMFError hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class CompositingError(DMFError):
    """Raised when a CompositeLayer/CompositeResult fails validation,
    or a requested mask_type isn't executed by this release. Carries
    every problem found, same discipline as every other *Error in this
    repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "compositing failed")
