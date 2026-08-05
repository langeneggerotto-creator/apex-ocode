"""Typed errors for the capability_atlas package, extending
core.errors' DMFError hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class CapabilityAtlasValidationError(DMFError):
    """Raised when a RendererCapability/RendererCapabilityProfile fails
    validation. Carries every problem found, same discipline as
    core.errors.ProjectValidationError, music.errors.TimelineValidationError,
    genome.errors.GenomeValidationError, and
    production.errors.ProductionGraphValidationError."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "capability atlas validation failed")
