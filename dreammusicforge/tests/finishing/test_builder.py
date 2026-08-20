from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.assembly.models import ExportManifest
from dreammusicforge.core.hashing import hash_file
from dreammusicforge.finishing.builder import DEFAULT_TARGET_LUFS, finish_film
from dreammusicforge.finishing.errors import FinishingError
from dreammusicforge.finishing.models import ColorAdjustment
from dreammusicforge.finishing.pipeline import measure_loudness

from .fixtures import FfmpegRequiredTestCase, make_clip_with_tone


def _manifest(output_file: Path) -> ExportManifest:
    return ExportManifest(
        id="EXPORT-test", master_song_id="AUDIO-test", master_song_hash="a" * 64,
        output_file=str(output_file), output_hash=hash_file(output_file),
        total_duration_seconds=3.0, created_at="2026-08-05T00:00:00+00:00",
    )


class FinishFilmTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        # a deliberately quiet clip, well below any reasonable target loudness
        self.clip = make_clip_with_tone(self.dir / "quiet.mp4", duration=3.0, volume=0.05)

    def tearDown(self):
        self._tmp.cleanup()

    def test_loudness_normalization_moves_measurably_toward_target(self):
        manifest = _manifest(self.clip)
        before = measure_loudness(self.clip)

        result = finish_film(manifest, self.dir / "work")

        self.assertTrue(result.id.startswith("FINISHING-"))
        self.assertEqual(result.target_lufs, DEFAULT_TARGET_LUFS)
        self.assertTrue(Path(result.output_file).exists())
        # the quiet source is well below -14 LUFS; after normalization the
        # measured loudness should have moved substantially closer to it.
        self.assertLess(
            abs(result.measured_loudness.integrated_lufs - DEFAULT_TARGET_LUFS),
            abs(before.integrated_lufs - DEFAULT_TARGET_LUFS),
        )

    def test_identity_color_adjustment_skips_the_color_pass(self):
        manifest = _manifest(self.clip)
        result = finish_film(manifest, self.dir / "work", color_adjustment=ColorAdjustment())
        self.assertTrue(result.output_file.endswith("loudness-normalized.mp4"))

    def test_non_identity_color_adjustment_produces_a_distinct_output(self):
        manifest = _manifest(self.clip)
        result = finish_film(manifest, self.dir / "work", color_adjustment=ColorAdjustment(contrast=1.5, saturation=1.5))
        self.assertTrue(result.output_file.endswith("color-adjusted.mp4"))
        self.assertFalse(result.color_adjustment.is_identity())

    def test_missing_source_file_raises(self):
        manifest = ExportManifest(
            id="EXPORT-test", master_song_id="AUDIO-test", master_song_hash="a" * 64,
            output_file=str(self.dir / "does-not-exist.mp4"), output_hash="b" * 64,
            total_duration_seconds=3.0, created_at="2026-08-05T00:00:00+00:00",
        )
        with self.assertRaises(FinishingError):
            finish_film(manifest, self.dir / "work")


if __name__ == "__main__":
    unittest.main()
