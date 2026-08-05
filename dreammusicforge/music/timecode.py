"""Timecode utilities: seconds <-> SMPTE-style HH:MM:SS:FF timecode, and
seconds <-> (bar, beat) given a tempo and time signature.

Bar/beat conversion is pure arithmetic from a constant tempo -- it does
not detect anything from audio. See music/beats.py's module docstring for
why that's an honest, deliberate scope boundary for this release, not an
oversight.
"""
from __future__ import annotations

from .errors import InvalidTimecodeError


def seconds_to_timecode(seconds: float, frame_rate: float) -> str:
    if seconds < 0:
        raise InvalidTimecodeError(f"seconds must be >= 0, got {seconds}")
    if frame_rate <= 0:
        raise InvalidTimecodeError(f"frame_rate must be > 0, got {frame_rate}")

    rounded_rate = round(frame_rate)
    total_frames = round(seconds * frame_rate)
    frames = total_frames % rounded_rate
    total_seconds = total_frames // rounded_rate
    secs = total_seconds % 60
    mins = (total_seconds // 60) % 60
    hours = total_seconds // 3600
    return f"{hours:02d}:{mins:02d}:{secs:02d}:{frames:02d}"


def timecode_to_seconds(timecode: str, frame_rate: float) -> float:
    if frame_rate <= 0:
        raise InvalidTimecodeError(f"frame_rate must be > 0, got {frame_rate}")

    parts = timecode.split(":")
    if len(parts) != 4 or not all(part.isdigit() for part in parts):
        raise InvalidTimecodeError(f"{timecode!r} is not a valid HH:MM:SS:FF timecode")

    hours, mins, secs, frames = (int(part) for part in parts)
    rounded_rate = round(frame_rate)
    if frames >= rounded_rate:
        raise InvalidTimecodeError(f"frame component {frames} is out of range for frame_rate {frame_rate} (max {rounded_rate - 1})")
    if mins >= 60 or secs >= 60:
        raise InvalidTimecodeError(f"{timecode!r} has an out-of-range minutes or seconds component")

    total_seconds = hours * 3600 + mins * 60 + secs
    total_frames = total_seconds * rounded_rate + frames
    return total_frames / frame_rate


def seconds_to_bar_beat(seconds: float, bpm: float, beats_per_bar: int) -> tuple[int, int]:
    """Returns (bar, beat_in_bar), both 1-based -- the first beat of the
    song is bar 1, beat 1."""
    if seconds < 0:
        raise InvalidTimecodeError(f"seconds must be >= 0, got {seconds}")
    if bpm <= 0:
        raise InvalidTimecodeError(f"bpm must be > 0, got {bpm}")
    if beats_per_bar <= 0:
        raise InvalidTimecodeError(f"beats_per_bar must be > 0, got {beats_per_bar}")

    beat_duration = 60.0 / bpm
    beat_index = int(seconds / beat_duration)  # 0-based global beat index
    bar = beat_index // beats_per_bar + 1
    beat_in_bar = beat_index % beats_per_bar + 1
    return bar, beat_in_bar
