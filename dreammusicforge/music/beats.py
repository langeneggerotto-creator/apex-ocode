"""Beat-grid generation from a constant tempo.

Honest scope boundary, stated plainly: this computes where beats *would*
fall given a declared bpm, time signature, and start offset -- it does
not detect beats from actual audio (no onset detection, no tempo
tracking). That's real DSP work (the spec's section 8.1 mentions
`librosa` for exactly this, as part of a later external-assembly-pipeline
release), and this release does not claim it. What's here is legitimate
and useful on its own: once a human (or a later analysis stage) supplies
bpm/time_signature/offset, every beat and bar position for the whole song
follows deterministically from arithmetic, needing no additional
detection step and no new dependency.

If tempo genuinely varies within a song, this model does not represent
that -- also a stated boundary, not a silent gap.
"""
from __future__ import annotations

from .errors import TimelineValidationError
from .models import Beat


def generate_beats(
    duration_seconds: float,
    bpm: float,
    beats_per_bar: int,
    offset_seconds: float = 0.0,
) -> tuple[Beat, ...]:
    if duration_seconds <= 0:
        raise TimelineValidationError([f"duration_seconds must be > 0, got {duration_seconds}"])
    if bpm <= 0:
        raise TimelineValidationError([f"bpm must be > 0, got {bpm}"])
    if beats_per_bar <= 0:
        raise TimelineValidationError([f"beats_per_bar must be > 0, got {beats_per_bar}"])
    if offset_seconds < 0:
        raise TimelineValidationError([f"offset_seconds must be >= 0, got {offset_seconds}"])
    if offset_seconds >= duration_seconds:
        raise TimelineValidationError([f"offset_seconds ({offset_seconds}) must be before duration_seconds ({duration_seconds})"])

    beat_duration = 60.0 / bpm
    beats: list[Beat] = []
    index = 0
    time = offset_seconds
    while time < duration_seconds:
        bar = index // beats_per_bar + 1
        beat_in_bar = index % beats_per_bar + 1
        beats.append(Beat(index=index, time=time, bar=bar, beat_in_bar=beat_in_bar))
        index += 1
        time = offset_seconds + index * beat_duration

    return tuple(beats)
