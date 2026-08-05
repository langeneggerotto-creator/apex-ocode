from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.assembly.pipeline import concatenate_clips, normalize_clip, replace_audio
from dreammusicforge.verification import inspect_media, measure_audio_rms

from .fixtures import FfmpegRequiredTestCase, make_clip, make_wav_tone


class NormalizeClipTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_rescales_to_target_resolution_and_frame_rate(self):
        clip = make_clip(self.dir / "a.mp4", size="720x1280", frame_rate=30.0, duration=2.0)
        output = self.dir / "normalized.mp4"
        normalize_clip(clip, output, width=512, height=910, frame_rate=24.0)
        media = inspect_media(output)
        self.assertEqual(media.width, 512)
        self.assertEqual(media.height, 910)
        self.assertAlmostEqual(media.frame_rate, 24.0, places=1)

    def test_strips_audio(self):
        clip = self.dir / "a.mp4"
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=red:size=480x854:d=2:r=24",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(clip),
        ], check=True, capture_output=True)
        output = self.dir / "normalized.mp4"
        normalize_clip(clip, output, width=480, height=854, frame_rate=24.0)
        media = inspect_media(output)
        self.assertFalse(media.has_audio)


class ConcatenateClipsTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_concatenates_same_format_clips_into_one_video(self):
        clip1 = make_clip(self.dir / "a.mp4", color="red", duration=2.0, size="480x854")
        clip2 = make_clip(self.dir / "b.mp4", color="blue", duration=3.0, size="480x854")
        norm1 = self.dir / "a-norm.mp4"
        norm2 = self.dir / "b-norm.mp4"
        normalize_clip(clip1, norm1, 480, 854, 24.0)
        normalize_clip(clip2, norm2, 480, 854, 24.0)

        output = self.dir / "concat.mp4"
        concatenate_clips((norm1, norm2), output)
        media = inspect_media(output)
        self.assertAlmostEqual(media.duration_seconds, 5.0, places=0)

    def test_joins_clips_with_originally_different_aspect_ratios(self):
        """Regression test for a real bug found running this against two
        differently-sourced clips: matching pixel dimensions alone isn't
        enough if the sources carry different sample-aspect-ratio
        metadata -- normalize_clip() must force square pixels or
        ffmpeg's concat filter refuses to join them."""
        clip1 = make_clip(self.dir / "a.mp4", size="480x854", duration=2.0)
        clip2 = make_clip(self.dir / "b.mp4", size="720x1280", duration=2.0)
        norm1 = self.dir / "a-norm.mp4"
        norm2 = self.dir / "b-norm.mp4"
        normalize_clip(clip1, norm1, 512, 910, 24.0)
        normalize_clip(clip2, norm2, 512, 910, 24.0)

        output = self.dir / "concat.mp4"
        concatenate_clips((norm1, norm2), output)  # must not raise
        media = inspect_media(output)
        self.assertEqual(media.width, 512)
        self.assertEqual(media.height, 910)


class ReplaceAudioTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_replaces_audio_with_the_master_song(self):
        clip = make_clip(self.dir / "video.mp4", duration=3.0)
        song = make_wav_tone(self.dir / "song.wav", duration=10.0)
        output = self.dir / "final.mp4"
        replace_audio(clip, song, output, duration_seconds=3.0)

        media = inspect_media(output)
        self.assertTrue(media.has_audio)
        self.assertAlmostEqual(media.duration_seconds, 3.0, places=0)
        audio = measure_audio_rms(output)
        self.assertFalse(audio.silent)

    def test_output_is_bounded_to_the_requested_duration_even_with_a_longer_song(self):
        clip = make_clip(self.dir / "video.mp4", duration=2.0)
        song = make_wav_tone(self.dir / "song.wav", duration=30.0)
        output = self.dir / "final.mp4"
        replace_audio(clip, song, output, duration_seconds=2.0)
        media = inspect_media(output)
        self.assertLess(media.duration_seconds, 3.0)


if __name__ == "__main__":
    unittest.main()
