from __future__ import annotations

import unittest

from dreammusicforge.finishing.models import ColorAdjustment, FinishingResult, LoudnessReport

LOUDNESS_DATA = {"integrated_lufs": -14.2, "true_peak_dbfs": -1.4, "loudness_range_lu": 6.0}
COLOR_DATA = {"brightness": 0.05, "contrast": 1.1, "saturation": 1.2}

RESULT_DATA = {
    "id": "FINISHING-deadbeef", "source_file": "in.mp4", "output_file": "out.mp4",
    "output_hash": "a" * 64, "target_lufs": -14.0,
    "measured_loudness": LOUDNESS_DATA, "color_adjustment": COLOR_DATA, "duration_seconds": 30.0,
}


class LoudnessReportRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        report = LoudnessReport.from_dict(LOUDNESS_DATA)
        self.assertEqual(report.to_dict(), LOUDNESS_DATA)


class ColorAdjustmentTests(unittest.TestCase):
    def test_default_is_identity(self):
        self.assertTrue(ColorAdjustment().is_identity())

    def test_non_default_is_not_identity(self):
        self.assertFalse(ColorAdjustment.from_dict(COLOR_DATA).is_identity())

    def test_from_dict_then_to_dict_round_trips(self):
        adjustment = ColorAdjustment.from_dict(COLOR_DATA)
        self.assertEqual(adjustment.to_dict(), COLOR_DATA)

    def test_missing_fields_default_to_identity_values(self):
        adjustment = ColorAdjustment.from_dict({})
        self.assertTrue(adjustment.is_identity())


class FinishingResultRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        result = FinishingResult.from_dict(RESULT_DATA)
        self.assertEqual(result.to_dict(), RESULT_DATA)

    def test_result_is_frozen(self):
        result = FinishingResult.from_dict(RESULT_DATA)
        with self.assertRaises(AttributeError):
            result.target_lufs = -20.0


if __name__ == "__main__":
    unittest.main()
