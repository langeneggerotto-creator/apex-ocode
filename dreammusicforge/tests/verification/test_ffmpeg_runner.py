from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dreammusicforge.verification.errors import FfmpegNotAvailableError, FfmpegRunError
from dreammusicforge.verification.ffmpeg_runner import (
    run_ffmpeg_astats, run_ffmpeg_extract_frame, run_ffmpeg_signalstats, run_ffmpeg_ssim, run_ffprobe_json,
)

from .fixtures import FfmpegRequiredTestCase, make_video


class MissingBinaryTests(unittest.TestCase):
    """These must pass with or without ffmpeg actually installed --
    they mock shutil.which() to simulate its absence, proving Release
    0.9 fails closed with a typed error rather than crashing with a
    raw FileNotFoundError or silently doing nothing."""

    def test_run_ffprobe_json_raises_when_ffprobe_missing(self):
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(FfmpegNotAvailableError):
                run_ffprobe_json(Path("/tmp/does-not-matter.mp4"))

    def test_run_ffmpeg_extract_frame_raises_when_ffmpeg_missing(self):
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(FfmpegNotAvailableError):
                run_ffmpeg_extract_frame(Path("/tmp/a.mp4"), 0.0, Path("/tmp/b.png"))

    def test_error_names_the_missing_binary(self):
        with mock.patch("shutil.which", return_value=None):
            try:
                run_ffprobe_json(Path("/tmp/does-not-matter.mp4"))
                self.fail("expected FfmpegNotAvailableError")
            except FfmpegNotAvailableError as exc:
                self.assertEqual(exc.binary_name, "ffprobe")


class RunFfprobeJsonTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_returns_real_probe_data(self):
        video = make_video(self.dir / "a.mp4", duration=1.0)
        probe = run_ffprobe_json(video)
        self.assertIn("streams", probe)
        self.assertIn("format", probe)

    def test_missing_file_raises(self):
        with self.assertRaises(FfmpegRunError):
            run_ffprobe_json(self.dir / "does-not-exist.mp4")


class RunFfmpegExtractFrameTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_produces_a_real_output_file(self):
        video = make_video(self.dir / "a.mp4", duration=1.0)
        output = self.dir / "frame.png"
        run_ffmpeg_extract_frame(video, 0.0, output)
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 0)


class RunFfmpegSsimTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_identical_frames_score_close_to_one(self):
        video = make_video(self.dir / "a.mp4", color="red", duration=1.0)
        frame = self.dir / "frame.png"
        run_ffmpeg_extract_frame(video, 0.0, frame)
        score = run_ffmpeg_ssim(frame, frame)
        self.assertAlmostEqual(score, 1.0, places=3)

    def test_different_colored_frames_score_lower(self):
        red_video = make_video(self.dir / "red.mp4", color="red", duration=1.0)
        blue_video = make_video(self.dir / "blue.mp4", color="blue", duration=1.0)
        red_frame = self.dir / "red.png"
        blue_frame = self.dir / "blue.png"
        run_ffmpeg_extract_frame(red_video, 0.0, red_frame)
        run_ffmpeg_extract_frame(blue_video, 0.0, blue_frame)
        score = run_ffmpeg_ssim(red_frame, blue_frame)
        self.assertLess(score, 1.0)


class RunFfmpegAstatsTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_returns_real_rms_and_peak(self):
        video = make_video(self.dir / "a.mp4", duration=1.0, with_audio=True)
        stats = run_ffmpeg_astats(video)
        self.assertIn("rms_level_db", stats)
        self.assertIn("peak_level_db", stats)
        self.assertLess(stats["rms_level_db"], 0.0)

    def test_silent_audio_has_very_low_rms(self):
        video = make_video(self.dir / "silent.mp4", duration=1.0, with_audio=True, silent_audio=True)
        stats = run_ffmpeg_astats(video)
        self.assertLess(stats["rms_level_db"], -50.0)


class RunFfmpegSignalstatsTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_returns_yuv_averages(self):
        video = make_video(self.dir / "a.mp4", color="red", duration=1.0)
        frame = self.dir / "frame.png"
        run_ffmpeg_extract_frame(video, 0.0, frame)
        stats = run_ffmpeg_signalstats(frame)
        self.assertIn("yavg", stats)
        self.assertIn("uavg", stats)
        self.assertIn("vavg", stats)


if __name__ == "__main__":
    unittest.main()
