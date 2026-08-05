from __future__ import annotations

import unittest

from dreammusicforge.music.errors import InvalidTimecodeError
from dreammusicforge.music.timecode import (
    seconds_to_bar_beat, seconds_to_timecode, timecode_to_seconds,
)


class SecondsToTimecodeTests(unittest.TestCase):
    def test_zero_seconds(self):
        self.assertEqual(seconds_to_timecode(0.0, 30), "00:00:00:00")

    def test_exact_seconds(self):
        self.assertEqual(seconds_to_timecode(61.0, 30), "00:01:01:00")

    def test_fractional_seconds_becomes_frames(self):
        self.assertEqual(seconds_to_timecode(1.5, 30), "00:00:01:15")

    def test_over_an_hour(self):
        self.assertEqual(seconds_to_timecode(3661.0, 30), "01:01:01:00")

    def test_negative_seconds_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            seconds_to_timecode(-1.0, 30)

    def test_zero_frame_rate_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            seconds_to_timecode(1.0, 0)


class TimecodeToSecondsTests(unittest.TestCase):
    def test_round_trips_with_seconds_to_timecode(self):
        self.assertAlmostEqual(timecode_to_seconds("00:01:01:15", 30), 61.5, places=6)

    def test_zero_timecode(self):
        self.assertEqual(timecode_to_seconds("00:00:00:00", 30), 0.0)

    def test_malformed_timecode_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            timecode_to_seconds("not-a-timecode", 30)

    def test_wrong_number_of_parts_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            timecode_to_seconds("00:01:01", 30)

    def test_out_of_range_frame_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            timecode_to_seconds("00:00:00:30", 30)

    def test_out_of_range_seconds_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            timecode_to_seconds("00:00:60:00", 30)

    def test_zero_frame_rate_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            timecode_to_seconds("00:00:00:00", 0)


class SecondsToBarBeatTests(unittest.TestCase):
    def test_first_beat_of_song(self):
        self.assertEqual(seconds_to_bar_beat(0.0, 120, 4), (1, 1))

    def test_second_beat(self):
        self.assertEqual(seconds_to_bar_beat(0.5, 120, 4), (1, 2))

    def test_second_bar(self):
        self.assertEqual(seconds_to_bar_beat(2.0, 120, 4), (2, 1))

    def test_negative_seconds_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            seconds_to_bar_beat(-1.0, 120, 4)

    def test_zero_bpm_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            seconds_to_bar_beat(1.0, 0, 4)

    def test_zero_beats_per_bar_raises(self):
        with self.assertRaises(InvalidTimecodeError):
            seconds_to_bar_beat(1.0, 120, 0)


if __name__ == "__main__":
    unittest.main()
