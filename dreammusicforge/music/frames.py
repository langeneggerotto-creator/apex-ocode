"""Seconds <-> frame-number conversion, per spec section 5's "frame
conversion" deliverable -- pure arithmetic, no dependency."""
from __future__ import annotations

from .errors import InvalidTimecodeError


def seconds_to_frame(seconds: float, frame_rate: float) -> int:
    if seconds < 0:
        raise InvalidTimecodeError(f"seconds must be >= 0, got {seconds}")
    if frame_rate <= 0:
        raise InvalidTimecodeError(f"frame_rate must be > 0, got {frame_rate}")
    return round(seconds * frame_rate)


def frame_to_seconds(frame: int, frame_rate: float) -> float:
    if frame < 0:
        raise InvalidTimecodeError(f"frame must be >= 0, got {frame}")
    if frame_rate <= 0:
        raise InvalidTimecodeError(f"frame_rate must be > 0, got {frame_rate}")
    return frame / frame_rate
