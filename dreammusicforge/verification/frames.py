"""extract_frame(): real frame extraction via ffmpeg -- the "frame
extraction" deliverable (spec section 19), used by seam comparison and
color-shift measurement to get an actual decoded still frame to work
from."""
from __future__ import annotations

from pathlib import Path

from .ffmpeg_runner import run_ffmpeg_extract_frame


def extract_frame(file_path: Path, timestamp_seconds: float, output_path: Path) -> Path:
    run_ffmpeg_extract_frame(file_path, timestamp_seconds, output_path)
    return output_path
