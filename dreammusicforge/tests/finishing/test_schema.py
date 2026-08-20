from __future__ import annotations

import unittest

from dreammusicforge.finishing.schema import (
    validate_color_adjustment_schema, validate_finishing_result_schema, validate_loudness_report_schema,
)

VALID_LOUDNESS = {"integrated_lufs": -14.2, "true_peak_dbfs": -1.4, "loudness_range_lu": 6.0}
VALID_COLOR = {"brightness": 0.0, "contrast": 1.0, "saturation": 1.0}
VALID_RESULT = {
    "id": "FINISHING-deadbeef", "source_file": "in.mp4", "output_file": "out.mp4",
    "output_hash": "a" * 64, "target_lufs": -14.0,
    "measured_loudness": VALID_LOUDNESS, "color_adjustment": VALID_COLOR, "duration_seconds": 30.0,
}


class LoudnessReportSchemaTests(unittest.TestCase):
    def test_valid_report_has_no_errors(self):
        self.assertEqual(validate_loudness_report_schema(VALID_LOUDNESS), [])

    def test_negative_range_is_rejected(self):
        data = dict(VALID_LOUDNESS, loudness_range_lu=-1.0)
        errors = validate_loudness_report_schema(data)
        self.assertTrue(any("loudness_range_lu" in e for e in errors))

    def test_non_number_is_rejected(self):
        data = dict(VALID_LOUDNESS, integrated_lufs="loud")
        errors = validate_loudness_report_schema(data)
        self.assertTrue(any("integrated_lufs" in e for e in errors))


class ColorAdjustmentSchemaTests(unittest.TestCase):
    def test_valid_adjustment_has_no_errors(self):
        self.assertEqual(validate_color_adjustment_schema(VALID_COLOR), [])

    def test_negative_contrast_is_rejected(self):
        data = dict(VALID_COLOR, contrast=-1.0)
        errors = validate_color_adjustment_schema(data)
        self.assertTrue(any("contrast" in e for e in errors))

    def test_empty_dict_is_valid(self):
        self.assertEqual(validate_color_adjustment_schema({}), [])


class FinishingResultSchemaTests(unittest.TestCase):
    def test_valid_result_has_no_errors(self):
        self.assertEqual(validate_finishing_result_schema(VALID_RESULT), [])

    def test_malformed_id_is_rejected(self):
        data = dict(VALID_RESULT, id="not-a-finishing-id")
        errors = validate_finishing_result_schema(data)
        self.assertTrue(any("id" in e for e in errors))

    def test_malformed_hash_is_rejected(self):
        data = dict(VALID_RESULT, output_hash="not-a-hash")
        errors = validate_finishing_result_schema(data)
        self.assertTrue(any("output_hash" in e for e in errors))

    def test_zero_duration_is_rejected(self):
        data = dict(VALID_RESULT, duration_seconds=0.0)
        errors = validate_finishing_result_schema(data)
        self.assertTrue(any("duration_seconds" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
