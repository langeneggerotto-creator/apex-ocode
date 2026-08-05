"""Shared real-media test fixtures: synthesized via ffmpeg's `lavfi`
test sources (solid color + sine tone), not external files -- these
tests validate against the same ffmpeg binary the production code
shells out to, no third-party test-data dependency."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


def ffmpeg_available() -> bool:
    import shutil
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def make_video(path: Path, color: str = "red", duration: float = 2.0, frame_rate: float = 24.0, size: str = "64x64", with_audio: bool = True, silent_audio: bool = False) -> Path:
    argv = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c={color}:size={size}:d={duration}:r={frame_rate}"]
    if with_audio:
        if silent_audio:
            argv += ["-f", "lavfi", "-i", f"anullsrc=sample_rate=44100:duration={duration}"]
        else:
            argv += ["-f", "lavfi", "-i", f"sine=frequency=1000:sample_rate=44100:duration={duration}"]
    argv += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    if with_audio:
        argv += ["-c:a", "aac"]
    else:
        argv += ["-an"]
    argv += [str(path)]
    subprocess.run(argv, check=True, capture_output=True)
    return path


@unittest.skipUnless(ffmpeg_available(), "ffmpeg/ffprobe not available in this environment")
class FfmpegRequiredTestCase(unittest.TestCase):
    """Base class for tests that need real ffmpeg/ffprobe -- skipped
    entirely (not failed) in an environment without them, since Release
    0.9 fails closed with FfmpegNotAvailableError rather than silently
    degrading, and that's covered separately by test_ffmpeg_runner.py's
    mocked-missing-binary test."""
