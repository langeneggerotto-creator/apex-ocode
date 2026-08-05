from __future__ import annotations

import unittest

from dreammusicforge.music.beats import generate_beats
from dreammusicforge.music.errors import TimelineValidationError
from dreammusicforge.music.models import Beat


class GenerateBeatsTests(unittest.TestCase):
    def test_first_beat_starts_at_offset(self):
        beats = generate_beats(2.0, 120, 4, offset_seconds=0.5)
        self.assertEqual(beats[0], Beat(index=0, time=0.5, bar=1, beat_in_bar=1))

    def test_beat_count_matches_tempo_and_duration(self):
        # 120 bpm = 0.5s/beat; 4 whole beats fit in 2.0s starting at 0
        beats = generate_beats(2.0, 120, 4)
        self.assertEqual(len(beats), 4)

    def test_bar_rolls_over_at_beats_per_bar(self):
        beats = generate_beats(3.0, 120, 4)
        bars = [beat.bar for beat in beats]
        self.assertEqual(bars, [1, 1, 1, 1, 2, 2])

    def test_beat_in_bar_cycles(self):
        beats = generate_beats(3.0, 120, 4)
        beat_positions = [beat.beat_in_bar for beat in beats]
        self.assertEqual(beat_positions, [1, 2, 3, 4, 1, 2])

    def test_indices_are_sequential_from_zero(self):
        beats = generate_beats(2.0, 120, 4)
        self.assertEqual([beat.index for beat in beats], list(range(len(beats))))

    def test_all_beats_strictly_before_duration(self):
        beats = generate_beats(2.0, 90, 3)
        self.assertTrue(all(beat.time < 2.0 for beat in beats))


class GenerateBeatsFailureTests(unittest.TestCase):
    def test_zero_duration_raises(self):
        with self.assertRaises(TimelineValidationError):
            generate_beats(0.0, 120, 4)

    def test_negative_duration_raises(self):
        with self.assertRaises(TimelineValidationError):
            generate_beats(-1.0, 120, 4)

    def test_zero_bpm_raises(self):
        with self.assertRaises(TimelineValidationError):
            generate_beats(2.0, 0, 4)

    def test_zero_beats_per_bar_raises(self):
        with self.assertRaises(TimelineValidationError):
            generate_beats(2.0, 120, 0)

    def test_negative_offset_raises(self):
        with self.assertRaises(TimelineValidationError):
            generate_beats(2.0, 120, 4, offset_seconds=-0.5)

    def test_offset_at_or_past_duration_raises(self):
        with self.assertRaises(TimelineValidationError):
            generate_beats(2.0, 120, 4, offset_seconds=2.0)

    def test_error_carries_message(self):
        try:
            generate_beats(0.0, 120, 4)
            self.fail("expected TimelineValidationError")
        except TimelineValidationError as exc:
            self.assertTrue(exc.errors)


if __name__ == "__main__":
    unittest.main()
