from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.verification.errors import FfmpegRunError
from dreammusicforge.verification.inspector import inspect_media

from .fixtures import FfmpegRequiredTestCase, make_video


class InspectMediaTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_reads_real_duration_frame_rate_and_resolution(self):
        video = make_video(self.dir / "a.mp4", duration=2.0, frame_rate=24.0, size="128x72")
        media = inspect_media(video)
        self.assertAlmostEqual(media.duration_seconds, 2.0, places=1)
        self.assertAlmostEqual(media.frame_rate, 24.0, places=1)
        self.assertEqual(media.width, 128)
        self.assertEqual(media.height, 72)
        self.assertEqual(media.video_codec, "h264")

    def test_detects_audio_presence(self):
        with_audio = make_video(self.dir / "with_audio.mp4", duration=1.0, with_audio=True)
        without_audio = make_video(self.dir / "without_audio.mp4", duration=1.0, with_audio=False)
        self.assertTrue(inspect_media(with_audio).has_audio)
        self.assertEqual(inspect_media(with_audio).audio_codec, "aac")
        self.assertFalse(inspect_media(without_audio).has_audio)
        self.assertIsNone(inspect_media(without_audio).audio_codec)

    def test_missing_file_raises(self):
        with self.assertRaises(FfmpegRunError):
            inspect_media(self.dir / "does-not-exist.mp4")


if __name__ == "__main__":
    unittest.main()
