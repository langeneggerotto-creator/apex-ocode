from __future__ import annotations

import unittest

from dreammusicforge.music.errors import InvalidTimecodeError
from dreammusicforge.music.frames import frame_to_seconds, seconds_to_frame


class SecondsToFrameTests(unittest.TestCase):
    def test_zero_seconds(self):
        self.assertEqual(seconds_to_frame(0.0, 30), 0)

    def test_one_second_at_30fps(self):
        self.assertEqual(seconds_to_frame(1.0, 30), 30)

    def test_rounds_to_nearest_frame(self):
        self.assertEqual(seconds_to_frame(1.0166, 30), 30)

    def test_negative_seconds_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            seconds_to_frame(-1.0, 30)

    def test_zero_frame_rate_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            seconds_to_frame(1.0, 0)


class FrameToSecondsTests(unittest.TestCase):
    def test_zero_frame(self):
        self.assertEqual(frame_to_seconds(0, 30), 0.0)

    def test_thirty_frames_at_30fps(self):
        self.assertEqual(frame_to_seconds(30, 30), 1.0)

    def test_round_trips_with_seconds_to_frame(self):
        self.assertEqual(frame_to_seconds(seconds_to_frame(2.0, 24), 24), 2.0)

    def test_negative_frame_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            frame_to_seconds(-1, 30)

    def test_zero_frame_rate_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            frame_to_seconds(1, 0)


if __name__ == "__main__":
    unittest.main()
