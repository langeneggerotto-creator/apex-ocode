from __future__ import annotations

import unittest

from dreammusicforge.compositing.models import CompositeLayer, CompositeResult

LAYER_DATA = {
    "layer_type": "foreground", "source_file": "fg.mp4", "mask_type": "chromakey",
    "chroma_color": "green", "chroma_similarity": 0.3, "chroma_blend": 0.1,
}

RESULT_DATA = {
    "id": "COMPOSITE-deadbeef", "shot_id": "SHOT-deadbeef", "output_file": "out.mp4",
    "output_hash": "a" * 64, "width": 480, "height": 854, "duration_seconds": 3.0,
    "layers": [
        {"layer_type": "background", "source_file": "bg.mp4", "mask_type": "none", "chroma_color": None, "chroma_similarity": 0.3, "chroma_blend": 0.1},
        LAYER_DATA,
    ],
}


class CompositeLayerRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        layer = CompositeLayer.from_dict(LAYER_DATA)
        self.assertEqual(layer.to_dict(), LAYER_DATA)

    def test_defaults_when_optional_fields_omitted(self):
        layer = CompositeLayer.from_dict({"layer_type": "background", "source_file": "bg.mp4"})
        self.assertEqual(layer.mask_type, "none")
        self.assertIsNone(layer.chroma_color)


class CompositeResultRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        result = CompositeResult.from_dict(RESULT_DATA)
        self.assertEqual(result.to_dict(), RESULT_DATA)

    def test_result_is_frozen(self):
        result = CompositeResult.from_dict(RESULT_DATA)
        with self.assertRaises(AttributeError):
            result.width = 100


if __name__ == "__main__":
    unittest.main()
