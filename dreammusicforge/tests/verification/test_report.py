from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.verification.errors import TechnicalVerificationError
from dreammusicforge.verification.frames import extract_frame
from dreammusicforge.verification.report import generate_technical_report

from .fixtures import FfmpegRequiredTestCase, make_video


class GenerateTechnicalReportTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_objective_technical_report_generated_from_video_files(self):
        """Release 0.9's stated acceptance test (spec section 19): an
        objective technical report generated from video files."""
        video = make_video(self.dir / "candidate.mp4", duration=2.0, frame_rate=24.0)
        report = generate_technical_report(
            candidate_id="CANDIDATE-deadbeef", file_path=video,
            expected_duration_seconds=2.0, expected_frame_rate=24.0,
        )

        self.assertEqual(report.candidate_id, "CANDIDATE-deadbeef")
        self.assertTrue(report.passed)
        self.assertEqual(report.failures, ())
        self.assertTrue(report.duration_frame_rate_check.within_tolerance)
        self.assertIsNotNone(report.audio_rms)
        self.assertFalse(report.audio_rms.silent)

    def test_duration_mismatch_fails_the_report(self):
        video = make_video(self.dir / "candidate.mp4", duration=2.0, frame_rate=24.0)
        report = generate_technical_report(
            candidate_id="CANDIDATE-deadbeef", file_path=video,
            expected_duration_seconds=10.0, expected_frame_rate=24.0,
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("duration_frame_rate" in failure for failure in report.failures))

    def test_silent_audio_fails_the_report(self):
        video = make_video(self.dir / "candidate.mp4", duration=1.0, frame_rate=24.0, with_audio=True, silent_audio=True)
        report = generate_technical_report(
            candidate_id="CANDIDATE-deadbeef", file_path=video,
            expected_duration_seconds=1.0, expected_frame_rate=24.0,
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("audio: silent" in failure for failure in report.failures))

    def test_missing_audio_fails_when_required(self):
        video = make_video(self.dir / "candidate.mp4", duration=1.0, frame_rate=24.0, with_audio=False)
        report = generate_technical_report(
            candidate_id="CANDIDATE-deadbeef", file_path=video,
            expected_duration_seconds=1.0, expected_frame_rate=24.0, require_audio=True,
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("audio: expected but missing" in failure for failure in report.failures))

    def test_missing_audio_is_allowed_when_not_required(self):
        video = make_video(self.dir / "candidate.mp4", duration=1.0, frame_rate=24.0, with_audio=False)
        report = generate_technical_report(
            candidate_id="CANDIDATE-deadbeef", file_path=video,
            expected_duration_seconds=1.0, expected_frame_rate=24.0, require_audio=False,
        )
        self.assertTrue(report.passed)

    def test_seam_and_color_comparison_against_a_matching_previous_frame_passes(self):
        video = make_video(self.dir / "candidate.mp4", color="red", duration=1.0, frame_rate=24.0)
        previous_frame = self.dir / "previous.png"
        extract_frame(video, 0.0, previous_frame)

        report = generate_technical_report(
            candidate_id="CANDIDATE-deadbeef", file_path=video,
            expected_duration_seconds=1.0, expected_frame_rate=24.0,
            previous_end_frame_path=previous_frame, frame_extraction_dir=self.dir,
        )
        self.assertTrue(report.passed)
        self.assertIsNotNone(report.seam_comparison)
        self.assertTrue(report.seam_comparison.similar)
        self.assertIsNotNone(report.color_shift)
        self.assertFalse(report.color_shift.shifted)

    def test_seam_and_color_comparison_against_a_mismatched_previous_frame_fails(self):
        video = make_video(self.dir / "candidate.mp4", color="red", duration=1.0, frame_rate=24.0)
        other_video = make_video(self.dir / "other.mp4", color="blue", duration=1.0)
        previous_frame = self.dir / "previous.png"
        extract_frame(other_video, 0.0, previous_frame)

        report = generate_technical_report(
            candidate_id="CANDIDATE-deadbeef", file_path=video,
            expected_duration_seconds=1.0, expected_frame_rate=24.0,
            previous_end_frame_path=previous_frame, frame_extraction_dir=self.dir,
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("seam" in failure for failure in report.failures))
        self.assertTrue(any("color" in failure for failure in report.failures))

    def test_previous_end_frame_without_extraction_dir_raises(self):
        video = make_video(self.dir / "candidate.mp4", duration=1.0, frame_rate=24.0)
        previous_frame = self.dir / "previous.png"
        extract_frame(video, 0.0, previous_frame)
        with self.assertRaises(TechnicalVerificationError):
            generate_technical_report(
                candidate_id="CANDIDATE-deadbeef", file_path=video,
                expected_duration_seconds=1.0, expected_frame_rate=24.0,
                previous_end_frame_path=previous_frame, frame_extraction_dir=None,
            )


if __name__ == "__main__":
    unittest.main()
