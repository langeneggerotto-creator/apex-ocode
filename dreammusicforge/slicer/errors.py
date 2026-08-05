"""Typed errors for the slicer package, extending core.errors' DMFError
hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class SlicerValidationError(DMFError):
    """Raised when a TemporalSlice/VisualLayer/MotionLayer/RenderTask
    fails validation. Carries every problem found, same discipline as
    every other *ValidationError in this repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "slicer validation failed")
