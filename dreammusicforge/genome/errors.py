"""Typed errors for the genome package, extending core.errors' DMFError
hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class GenomeValidationError(DMFError):
    """Raised when a Performer/Costume/World/FilmGenome fails validation.
    Carries every problem found, same discipline as
    core.errors.ProjectValidationError and music.errors.TimelineValidationError."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "genome validation failed")
