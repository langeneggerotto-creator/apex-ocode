"""Typed errors for the verification package, extending core.errors'
DMFError hierarchy rather than starting a parallel one."""
from __future__ import annotations

from ..core.errors import DMFError


class FfmpegNotAvailableError(DMFError):
    """Raised when ffmpeg or ffprobe isn't on PATH. This package is the
    first in this repository to depend on an external binary rather than
    stdlib alone -- see verification/ffmpeg_runner.py's module docstring
    for why, and README.md's "Design choices" section for the disclosure."""

    def __init__(self, binary_name: str):
        self.binary_name = binary_name
        super().__init__(f"{binary_name!r} is not on PATH -- Release 0.9 requires ffmpeg and ffprobe to be installed")


class FfmpegRunError(DMFError):
    """Raised when an ffmpeg/ffprobe invocation fails or returns output
    this package can't parse. Carries every problem found, same
    discipline as every other *ValidationError in this repository."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "ffmpeg/ffprobe invocation failed")


class TechnicalVerificationError(DMFError):
    """Raised when a TechnicalReport fails validation."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "technical verification failed")
