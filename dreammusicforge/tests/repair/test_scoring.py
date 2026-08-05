from __future__ import annotations

import unittest

from dreammusicforge.repair.scoring import score_technical_report
from dreammusicforge.verification.models import (
    AudioRmsReport, ColorShiftReport, DurationFrameRateCheck, MediaMetadata, SeamComparison, TechnicalReport,
)

MEDIA = MediaMetadata(duration_seconds=10.0, frame_rate=24.0, width=720, height=1280, video_codec="h264", has_audio=True, audio_codec="aac")


def _duration_check(within_tolerance=True):
    return DurationFrameRateCheck(
        expected_duration_seconds=10.0, measured_duration_seconds=10.0 if within_tolerance else 15.0,
        expected_frame_rate=24.0, measured_frame_rate=24.0, duration_tolerance_seconds=0.5,
        frame_rate_tolerance=0.5, within_tolerance=within_tolerance,
    )


class ScoreTechnicalReportTests(unittest.TestCase):
    def test_within_tolerance_scores_100(self):
        report = TechnicalReport(
            candidate_id="CANDIDATE-x", file="a.mp4", media=MEDIA, duration_frame_rate_check=_duration_check(True),
            audio_rms=None, seam_comparison=None, color_shift=None, passed=True, failures=(),
        )
        metrics = score_technical_report(report)
        self.assertEqual(metrics["duration_frame_rate"], 100.0)

    def test_out_of_tolerance_scores_zero(self):
        report = TechnicalReport(
            candidate_id="CANDIDATE-x", file="a.mp4", media=MEDIA, duration_frame_rate_check=_duration_check(False),
            audio_rms=None, seam_comparison=None, color_shift=None, passed=False, failures=("duration_frame_rate: mismatch",),
        )
        metrics = score_technical_report(report)
        self.assertEqual(metrics["duration_frame_rate"], 0.0)

    def test_silent_audio_scores_zero(self):
        report = TechnicalReport(
            candidate_id="CANDIDATE-x", file="a.mp4", media=MEDIA, duration_frame_rate_check=_duration_check(True),
            audio_rms=AudioRmsReport(rms_level_db=-90.0, peak_level_db=-80.0, silent=True),
            seam_comparison=None, color_shift=None, passed=False, failures=("audio: silent",),
        )
        metrics = score_technical_report(report)
        self.assertEqual(metrics["audio"], 0.0)

    def test_audible_audio_scores_100(self):
        report = TechnicalReport(
            candidate_id="CANDIDATE-x", file="a.mp4", media=MEDIA, duration_frame_rate_check=_duration_check(True),
            audio_rms=AudioRmsReport(rms_level_db=-18.0, peak_level_db=-3.0, silent=False),
            seam_comparison=None, color_shift=None, passed=True, failures=(),
        )
        metrics = score_technical_report(report)
        self.assertEqual(metrics["audio"], 100.0)

    def test_missing_required_audio_scores_zero(self):
        report = TechnicalReport(
            candidate_id="CANDIDATE-x", file="a.mp4", media=MEDIA, duration_frame_rate_check=_duration_check(True),
            audio_rms=None, seam_comparison=None, color_shift=None, passed=False,
            failures=("audio: expected but missing from this candidate",),
        )
        metrics = score_technical_report(report)
        self.assertEqual(metrics["audio"], 0.0)

    def test_no_audio_signal_at_all_omits_the_metric(self):
        report = TechnicalReport(
            candidate_id="CANDIDATE-x", file="a.mp4", media=MEDIA, duration_frame_rate_check=_duration_check(True),
            audio_rms=None, seam_comparison=None, color_shift=None, passed=True, failures=(),
        )
        metrics = score_technical_report(report)
        self.assertNotIn("audio", metrics)

    def test_seam_comparison_maps_ssim_to_a_0_100_scale(self):
        report = TechnicalReport(
            candidate_id="CANDIDATE-x", file="a.mp4", media=MEDIA, duration_frame_rate_check=_duration_check(True),
            audio_rms=None, seam_comparison=SeamComparison(ssim_score=0.67374, similar=False),
            color_shift=None, passed=False, failures=("seam: dissimilar",),
        )
        metrics = score_technical_report(report)
        self.assertAlmostEqual(metrics["continuity"], 67.374, places=3)

    def test_no_seam_comparison_omits_continuity_metric(self):
        report = TechnicalReport(
            candidate_id="CANDIDATE-x", file="a.mp4", media=MEDIA, duration_frame_rate_check=_duration_check(True),
            audio_rms=None, seam_comparison=None, color_shift=None, passed=True, failures=(),
        )
        metrics = score_technical_report(report)
        self.assertNotIn("continuity", metrics)

    def test_color_shift_is_inverted_into_a_score(self):
        report = TechnicalReport(
            candidate_id="CANDIDATE-x", file="a.mp4", media=MEDIA, duration_frame_rate_check=_duration_check(True),
            audio_rms=None, seam_comparison=None, color_shift=ColorShiftReport(delta_y=6.0, delta_u=3.0, delta_v=2.0, shifted=False),
            passed=True, failures=(),
        )
        metrics = score_technical_report(report)
        self.assertEqual(metrics["color_continuity"], 94.0)

    def test_extreme_color_shift_floors_at_zero(self):
        report = TechnicalReport(
            candidate_id="CANDIDATE-x", file="a.mp4", media=MEDIA, duration_frame_rate_check=_duration_check(True),
            audio_rms=None, seam_comparison=None, color_shift=ColorShiftReport(delta_y=255.0, delta_u=0.0, delta_v=0.0, shifted=True),
            passed=False, failures=("color: shifted",),
        )
        metrics = score_technical_report(report)
        self.assertEqual(metrics["color_continuity"], 0.0)


if __name__ == "__main__":
    unittest.main()
