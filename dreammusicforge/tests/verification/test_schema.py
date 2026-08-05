from __future__ import annotations

import copy
import unittest

from dreammusicforge.verification.schema import (
    validate_audio_rms_report_schema, validate_color_shift_report_schema,
    validate_duration_frame_rate_check_schema, validate_media_metadata_schema, validate_seam_comparison_schema,
    validate_technical_report_schema,
)

MEDIA_DATA = {
    "duration_seconds": 6.5, "frame_rate": 24.0, "width": 1920, "height": 1080,
    "video_codec": "h264", "has_audio": True, "audio_codec": "aac",
}
DURATION_CHECK_DATA = {
    "expected_duration_seconds": 6.5, "measured_duration_seconds": 6.5, "expected_frame_rate": 24.0,
    "measured_frame_rate": 24.0, "duration_tolerance_seconds": 0.5, "frame_rate_tolerance": 0.5,
    "within_tolerance": True,
}
AUDIO_RMS_DATA = {"rms_level_db": -20.0, "peak_level_db": -6.0, "silent": False}
SEAM_DATA = {"ssim_score": 0.95, "similar": True}
COLOR_SHIFT_DATA = {"delta_y": 2.0, "delta_u": 1.0, "delta_v": 1.5, "shifted": False}

VALID_REPORT = {
    "candidate_id": "CANDIDATE-deadbeef", "file": "renders/CANDIDATE-deadbeef.mp4", "media": MEDIA_DATA,
    "duration_frame_rate_check": DURATION_CHECK_DATA, "passed": True, "failures": [],
}


class MediaMetadataSchemaTests(unittest.TestCase):
    def test_valid_media_has_no_errors(self):
        self.assertEqual(validate_media_metadata_schema(MEDIA_DATA), [])

    def test_zero_duration_is_rejected(self):
        data = dict(MEDIA_DATA, duration_seconds=0)
        errors = validate_media_metadata_schema(data)
        self.assertTrue(any("duration_seconds" in e for e in errors))

    def test_has_audio_true_without_codec_is_rejected(self):
        data = dict(MEDIA_DATA, audio_codec=None)
        errors = validate_media_metadata_schema(data)
        self.assertTrue(any("audio_codec" in e for e in errors))

    def test_has_audio_false_with_null_codec_is_valid(self):
        data = dict(MEDIA_DATA, has_audio=False, audio_codec=None)
        self.assertEqual(validate_media_metadata_schema(data), [])


class DurationFrameRateCheckSchemaTests(unittest.TestCase):
    def test_valid_check_has_no_errors(self):
        self.assertEqual(validate_duration_frame_rate_check_schema(DURATION_CHECK_DATA), [])

    def test_missing_field_is_reported(self):
        data = copy.deepcopy(DURATION_CHECK_DATA)
        del data["measured_duration_seconds"]
        errors = validate_duration_frame_rate_check_schema(data)
        self.assertTrue(any("measured_duration_seconds" in e for e in errors))


class AudioRmsReportSchemaTests(unittest.TestCase):
    def test_valid_report_has_no_errors(self):
        self.assertEqual(validate_audio_rms_report_schema(AUDIO_RMS_DATA), [])

    def test_negative_infinity_is_accepted_as_a_number(self):
        data = dict(AUDIO_RMS_DATA, rms_level_db=float("-inf"))
        self.assertEqual(validate_audio_rms_report_schema(data), [])


class SeamComparisonSchemaTests(unittest.TestCase):
    def test_valid_seam_has_no_errors(self):
        self.assertEqual(validate_seam_comparison_schema(SEAM_DATA), [])

    def test_out_of_range_ssim_is_rejected(self):
        data = dict(SEAM_DATA, ssim_score=1.5)
        errors = validate_seam_comparison_schema(data)
        self.assertTrue(any("ssim_score" in e for e in errors))


class ColorShiftReportSchemaTests(unittest.TestCase):
    def test_valid_shift_has_no_errors(self):
        self.assertEqual(validate_color_shift_report_schema(COLOR_SHIFT_DATA), [])

    def test_negative_delta_is_rejected(self):
        data = dict(COLOR_SHIFT_DATA, delta_y=-1.0)
        errors = validate_color_shift_report_schema(data)
        self.assertTrue(any("delta_y" in e for e in errors))


class TechnicalReportSchemaTests(unittest.TestCase):
    def test_valid_report_has_no_errors(self):
        self.assertEqual(validate_technical_report_schema(VALID_REPORT), [])

    def test_passed_true_with_failures_is_rejected(self):
        data = dict(VALID_REPORT, passed=True, failures=["something broke"])
        errors = validate_technical_report_schema(data)
        self.assertTrue(any("passed is true but failures" in e for e in errors))

    def test_passed_false_without_failures_is_rejected(self):
        data = dict(VALID_REPORT, passed=False, failures=[])
        errors = validate_technical_report_schema(data)
        self.assertTrue(any("passed is false but failures" in e for e in errors))

    def test_passed_false_with_failures_is_valid(self):
        data = dict(VALID_REPORT, passed=False, failures=["duration mismatch"])
        self.assertEqual(validate_technical_report_schema(data), [])

    def test_invalid_nested_media_is_reported(self):
        data = dict(VALID_REPORT, media=dict(MEDIA_DATA, duration_seconds=0))
        errors = validate_technical_report_schema(data)
        self.assertTrue(any(e.startswith("media:") for e in errors))

    def test_optional_sections_may_be_omitted(self):
        self.assertEqual(validate_technical_report_schema(VALID_REPORT), [])

    def test_invalid_optional_seam_section_is_reported(self):
        data = dict(VALID_REPORT, seam_comparison={"ssim_score": 5.0, "similar": True})
        errors = validate_technical_report_schema(data)
        self.assertTrue(any(e.startswith("seam_comparison:") for e in errors))


if __name__ == "__main__":
    unittest.main()
