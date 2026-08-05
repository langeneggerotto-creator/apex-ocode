from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.verification.color import COLOR_SHIFT_THRESHOLD, measure_color_shift
from dreammusicforge.verification.frames import extract_frame

from .fixtures import FfmpegRequiredTestCase, make_video


class MeasureColorShiftTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_identical_frames_have_zero_shift(self):
        video = make_video(self.dir / "a.mp4", color="red", duration=1.0)
        frame = self.dir / "frame.png"
        extract_frame(video, 0.0, frame)
        shift = measure_color_shift(frame, frame)
        self.assertFalse(shift.shifted)
        self.assertEqual(shift.delta_y, 0.0)

    def test_different_colors_are_flagged_as_shifted(self):
        red_video = make_video(self.dir / "red.mp4", color="red", duration=1.0)
        blue_video = make_video(self.dir / "blue.mp4", color="blue", duration=1.0)
        red_frame = self.dir / "red.png"
        blue_frame = self.dir / "blue.png"
        extract_frame(red_video, 0.0, red_frame)
        extract_frame(blue_video, 0.0, blue_frame)
        shift = measure_color_shift(red_frame, blue_frame)
        self.assertTrue(shift.shifted)
        self.assertGreaterEqual(max(shift.delta_y, shift.delta_u, shift.delta_v), COLOR_SHIFT_THRESHOLD)


if __name__ == "__main__":
    unittest.main()
