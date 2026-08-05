"""Typed errors for the providers.kling package, extending
core.errors' DMFError hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ...core.errors import DMFError


class KlingCompilerError(DMFError):
    """Raised when a KlingPackage can't be compiled -- an unsupported
    mode, a duration exceeding the profile's limit, or a failed
    validation. Carries every problem found, same discipline as every
    other *ValidationError in this repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "Kling compiler validation failed")
