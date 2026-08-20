from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from dreammusicforge.compositing.builder import build_composite
from dreammusicforge.compositing.errors import CompositingError
from dreammusicforge.compositing.models import CompositeLayer

from .fixtures import FfmpegRequiredTestCase, make_clip


def _average_pixel_rgb(path: Path) -> tuple[int, int, int]:
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vframes", "1", "-vf", "scale=1:1",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        check=True, capture_output=True,
    )
    return tuple(result.stdout[:3])


class BuildCompositeTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_chromakey_fully_keyed_foreground_shows_only_background(self):
        background = make_clip(self.dir / "bg.mp4", color="red", size="64x64", duration=1.0)
        foreground = make_clip(self.dir / "fg.mp4", color="green", size="64x64", duration=1.0)
        bg_layer = CompositeLayer(layer_type="background", source_file=str(background))
        fg_layer = CompositeLayer(layer_type="foreground", source_file=str(foreground), mask_type="chromakey", chroma_color="green")

        result = build_composite("SHOT-1", bg_layer, fg_layer, self.dir / "work")

        self.assertTrue(result.id.startswith("COMPOSITE-"))
        self.assertEqual(len(result.layers), 2)
        r, g, b = _average_pixel_rgb(Path(result.output_file))
        self.assertGreater(r, g, "a fully-keyed-out green foreground should leave the red background visible")

    def test_none_mask_type_opaquely_overlays_foreground(self):
        background = make_clip(self.dir / "bg.mp4", color="red", size="64x64", duration=1.0)
        foreground = make_clip(self.dir / "fg.mp4", color="blue", size="64x64", duration=1.0)
        bg_layer = CompositeLayer(layer_type="background", source_file=str(background))
        fg_layer = CompositeLayer(layer_type="foreground", source_file=str(foreground), mask_type="none")

        result = build_composite("SHOT-2", bg_layer, fg_layer, self.dir / "work")
        r, g, b = _average_pixel_rgb(Path(result.output_file))
        self.assertGreater(b, r, "an opaque full-frame foreground overlay should hide the background entirely")

    def test_non_executable_mask_type_raises(self):
        background = make_clip(self.dir / "bg.mp4", color="red", size="64x64", duration=1.0)
        foreground = make_clip(self.dir / "fg.mp4", color="green", size="64x64", duration=1.0)
        bg_layer = CompositeLayer(layer_type="background", source_file=str(background))
        fg_layer = CompositeLayer(layer_type="foreground", source_file=str(foreground), mask_type="alpha_channel")

        with self.assertRaises(CompositingError):
            build_composite("SHOT-3", bg_layer, fg_layer, self.dir / "work")

    def test_swapped_layer_types_raise(self):
        background = make_clip(self.dir / "bg.mp4", color="red", size="64x64", duration=1.0)
        foreground = make_clip(self.dir / "fg.mp4", color="green", size="64x64", duration=1.0)
        # deliberately swapped: layer_type doesn't match the role it's passed as
        bg_layer = CompositeLayer(layer_type="foreground", source_file=str(background))
        fg_layer = CompositeLayer(layer_type="background", source_file=str(foreground), mask_type="none")

        with self.assertRaises(CompositingError):
            build_composite("SHOT-4", bg_layer, fg_layer, self.dir / "work")


if __name__ == "__main__":
    unittest.main()
