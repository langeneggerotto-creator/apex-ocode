"""Real audio metadata inspection -- stdlib `wave` module only. Reads
duration, sample rate, channel count, and sample width directly from a
WAV file's header, no third-party dependency.

Deliberately WAV-only, not a general audio-format prober: spec section
6.2's example source_file is a .wav, and a general-purpose decoder
(handling mp3/aac/flac/etc.) needs either ffmpeg as an external binary
dependency or a third-party Python package, neither of which this
release introduces speculatively. See music/README note (in the package
docstring) for what a later release adding real DSP/tempo-detection would
need instead.
"""
from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path

from .errors import AudioInspectionError


@dataclass(frozen=True)
class WavMetadata:
    duration_seconds: float
    sample_rate: int
    channels: int
    sample_width_bytes: int


def inspect_wav(path: Path) -> WavMetadata:
    if not path.is_file():
        raise AudioInspectionError(f"no such audio file: {path}")

    try:
        with wave.open(str(path), "rb") as handle:
            frame_count = handle.getnframes()
            sample_rate = handle.getframerate()
            channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
    except (wave.Error, EOFError, OSError) as exc:
        raise AudioInspectionError(f"{path} is not a readable WAV file: {exc}") from exc

    if sample_rate <= 0:
        raise AudioInspectionError(f"{path} reports a non-positive sample rate: {sample_rate}")
    if frame_count <= 0:
        raise AudioInspectionError(f"{path} contains zero audio frames")

    return WavMetadata(
        duration_seconds=frame_count / float(sample_rate),
        sample_rate=sample_rate,
        channels=channels,
        sample_width_bytes=sample_width,
    )
