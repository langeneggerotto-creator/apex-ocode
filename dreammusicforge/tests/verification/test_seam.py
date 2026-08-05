from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.verification.frames import extract_frame
from dreammusicforge.verification.seam import SSIM_SIMILARITY_THRESHOLD, compare_seam

from .fixtures import FfmpegRequiredTestCase, make_video


class CompareSeamTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_identical_frames_are_similar(self):
        video = make_video(self.dir / "a.mp4", color="red", duration=1.0)
        frame = self.dir / "frame.png"
        extract_frame(video, 0.0, frame)
        comparison = compare_seam(frame, frame)
        self.assertTrue(comparison.similar)
        self.assertGreaterEqual(comparison.ssim_score, SSIM_SIMILARITY_THRESHOLD)

    def test_very_different_frames_are_not_similar(self):
        red_video = make_video(self.dir / "red.mp4", color="red", duration=1.0)
        blue_video = make_video(self.dir / "blue.mp4", color="blue", duration=1.0)
        red_frame = self.dir / "red.png"
        blue_frame = self.dir / "blue.png"
        extract_frame(red_video, 0.0, red_frame)
        extract_frame(blue_video, 0.0, blue_frame)
        comparison = compare_seam(red_frame, blue_frame)
        self.assertFalse(comparison.similar)
        self.assertLess(comparison.ssim_score, SSIM_SIMILARITY_THRESHOLD)


if __name__ == "__main__":
    unittest.main()
