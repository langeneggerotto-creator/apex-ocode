"""measure_audio_rms(): real audio RMS measurement via ffmpeg's `astats`
filter -- the "audio RMS" deliverable (spec section 19), covering spec
section 9.1's "silence" and "loudness" technical checks.

SILENCE_RMS_THRESHOLD_DB is this release's own choice (-60 dBFS) --
conventional for "no audibly meaningful signal," not a spec-given
number. This is the exact class of measurement that root-caused a real
"no audio in the stitched video" bug in the sibling agentic-twin
repository's DreamMusicForge session (a timestamp-discontinuity bug
during stream-copy concatenation, found via this same astats technique)
-- this function generalizes that diagnostic into the pipeline itself
rather than a one-off manual check.
"""
from __future__ import annotations

from pathlib import Path

from .ffmpeg_runner import run_ffmpeg_astats
from .models import AudioRmsReport

SILENCE_RMS_THRESHOLD_DB = -60.0


def measure_audio_rms(file_path: Path) -> AudioRmsReport:
    stats = run_ffmpeg_astats(file_path)
    rms_level_db = stats["rms_level_db"]
    return AudioRmsReport(
        rms_level_db=rms_level_db, peak_level_db=stats["peak_level_db"],
        silent=rms_level_db <= SILENCE_RMS_THRESHOLD_DB,
    )
