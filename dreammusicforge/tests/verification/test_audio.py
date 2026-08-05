from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.verification.audio import SILENCE_RMS_THRESHOLD_DB, measure_audio_rms

from .fixtures import FfmpegRequiredTestCase, make_video


class MeasureAudioRmsTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_audible_tone_is_not_silent(self):
        video = make_video(self.dir / "a.mp4", duration=1.0, with_audio=True)
        report = measure_audio_rms(video)
        self.assertFalse(report.silent)
        self.assertGreater(report.rms_level_db, SILENCE_RMS_THRESHOLD_DB)

    def test_silent_track_is_detected(self):
        """This is the exact class of bug (silent audio in a rendered
        clip) that a real diagnostic session in the sibling agentic-twin
        repository root-caused to a stream-copy timestamp discontinuity
        -- this test proves the same astats-based detection generalizes
        into this pipeline."""
        video = make_video(self.dir / "silent.mp4", duration=1.0, with_audio=True, silent_audio=True)
        report = measure_audio_rms(video)
        self.assertTrue(report.silent)


if __name__ == "__main__":
    unittest.main()
