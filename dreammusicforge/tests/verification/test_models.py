from __future__ import annotations

import unittest

from dreammusicforge.verification.models import (
    AudioRmsReport, ColorShiftReport, DurationFrameRateCheck, MediaMetadata, SeamComparison, TechnicalReport,
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

TECHNICAL_REPORT_DATA = {
    "candidate_id": "CANDIDATE-deadbeef", "file": "renders/CANDIDATE-deadbeef.mp4", "media": MEDIA_DATA,
    "duration_frame_rate_check": DURATION_CHECK_DATA, "audio_rms": AUDIO_RMS_DATA, "seam_comparison": SEAM_DATA,
    "color_shift": COLOR_SHIFT_DATA, "passed": True, "failures": [],
}


class MediaMetadataRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        media = MediaMetadata.from_dict(MEDIA_DATA)
        self.assertEqual(media.to_dict(), MEDIA_DATA)

    def test_missing_audio_codec_defaults_to_none(self):
        data = {k: v for k, v in MEDIA_DATA.items() if k != "audio_codec"}
        media = MediaMetadata.from_dict(data)
        self.assertIsNone(media.audio_codec)


class DurationFrameRateCheckRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        check = DurationFrameRateCheck.from_dict(DURATION_CHECK_DATA)
        self.assertEqual(check.to_dict(), DURATION_CHECK_DATA)


class AudioRmsReportRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        report = AudioRmsReport.from_dict(AUDIO_RMS_DATA)
        self.assertEqual(report.to_dict(), AUDIO_RMS_DATA)


class SeamComparisonRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        seam = SeamComparison.from_dict(SEAM_DATA)
        self.assertEqual(seam.to_dict(), SEAM_DATA)


class ColorShiftReportRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        shift = ColorShiftReport.from_dict(COLOR_SHIFT_DATA)
        self.assertEqual(shift.to_dict(), COLOR_SHIFT_DATA)


class TechnicalReportRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        report = TechnicalReport.from_dict(TECHNICAL_REPORT_DATA)
        self.assertEqual(report.to_dict(), TECHNICAL_REPORT_DATA)

    def test_optional_sections_may_be_none(self):
        data = dict(TECHNICAL_REPORT_DATA, audio_rms=None, seam_comparison=None, color_shift=None)
        report = TechnicalReport.from_dict(data)
        self.assertIsNone(report.audio_rms)
        self.assertIsNone(report.seam_comparison)
        self.assertIsNone(report.color_shift)

    def test_report_is_frozen(self):
        report = TechnicalReport.from_dict(TECHNICAL_REPORT_DATA)
        with self.assertRaises(Exception):
            report.passed = False  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
