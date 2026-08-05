"""Typed errors for the music/timeline package, extending core.errors'
DMFError hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class AudioInspectionError(DMFError):
    """Raised when a source audio file can't be read or contains no
    usable audio (zero frames, zero sample rate)."""


class InvalidTimecodeError(DMFError):
    """Raised when a timecode string is malformed or its frame component
    is out of range for the given frame rate."""


class TimelineValidationError(DMFError):
    """Raised when a MasterSong/Section/Beat/LyricLine timeline fails
    validation. Carries every error found, same discipline as
    core.errors.ProjectValidationError."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "timeline validation failed")
