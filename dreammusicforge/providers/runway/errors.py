"""Typed errors for the providers.runway package, extending
core.errors' DMFError hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ...core.errors import DMFError


class RunwayCompilerError(DMFError):
    """Raised when a RunwayPackage can't be compiled -- an unsupported
    mode, a duration not in the profile's discrete allowed set, or a
    failed validation. Carries every problem found, same discipline as
    every other *ValidationError in this repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "Runway compiler validation failed")


class RunwayClientError(DMFError):
    """Raised by providers.runway.client when a real API call can't be
    made or fails -- a missing API key, a network/HTTP error, or a
    task that finishes with status FAILED. Carries every problem
    found, same discipline as every other *Error in this repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "Runway API call failed")
