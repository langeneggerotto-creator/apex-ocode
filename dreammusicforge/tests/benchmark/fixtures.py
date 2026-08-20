"""Shared real-media test fixtures for the Release 1.0 end-to-end
benchmark: synthesized via ffmpeg's `lavfi` test sources, not external
files -- same approach as every other package's tests/*/fixtures.py."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


def ffmpeg_available() -> bool:
    import shutil
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def make_clip_with_tone(
    path: Path, color: str = "red", duration: float = 3.0, frame_rate: float = 24.0,
    size: str = "480x854", frequency: int = 440,
) -> Path:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", f"color=c={color}:size={size}:d={duration}:r={frame_rate}",
        "-f", "lavfi", "-i", f"sine=frequency={frequency}:sample_rate=44100:duration={duration}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path),
    ], check=True, capture_output=True)
    return path


def make_wav_tone(path: Path, duration: float = 10.0, frequency: int = 440) -> Path:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=frequency={frequency}:sample_rate=44100:duration={duration}",
        "-ac", "2", str(path),
    ], check=True, capture_output=True)
    return path


@unittest.skipUnless(ffmpeg_available(), "ffmpeg/ffprobe not available in this environment")
class FfmpegRequiredTestCase(unittest.TestCase):
    """Base class for tests that need real ffmpeg -- skipped entirely
    (not failed) in an environment without it."""
