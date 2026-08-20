"""Shared real-media test fixtures: synthesized via ffmpeg's `lavfi`
test sources, not external files -- same approach as
tests/assembly/fixtures.py."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


def ffmpeg_available() -> bool:
    import shutil
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def make_clip_with_tone(path: Path, duration: float = 3.0, frequency: int = 440, volume: float = 0.5, size: str = "320x240") -> Path:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", f"color=c=red:size={size}:d={duration}:r=24",
        "-f", "lavfi", "-i", f"sine=frequency={frequency}:sample_rate=44100:duration={duration}",
        "-af", f"volume={volume}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path),
    ], check=True, capture_output=True)
    return path


@unittest.skipUnless(ffmpeg_available(), "ffmpeg/ffprobe not available in this environment")
class FfmpegRequiredTestCase(unittest.TestCase):
    """Base class for tests that need real ffmpeg -- skipped entirely
    (not failed) in an environment without it."""
