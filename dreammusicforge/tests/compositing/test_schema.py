from __future__ import annotations

import unittest

from dreammusicforge.compositing.schema import validate_composite_layer_schema, validate_composite_result_schema

BACKGROUND = {"layer_type": "background", "source_file": "bg.mp4", "mask_type": "none", "chroma_color": None, "chroma_similarity": 0.3, "chroma_blend": 0.1}
FOREGROUND = {"layer_type": "foreground", "source_file": "fg.mp4", "mask_type": "chromakey", "chroma_color": "green", "chroma_similarity": 0.3, "chroma_blend": 0.1}

VALID_RESULT = {
    "id": "COMPOSITE-deadbeef", "shot_id": "SHOT-deadbeef", "output_file": "out.mp4",
    "output_hash": "a" * 64, "width": 480, "height": 854, "duration_seconds": 3.0,
    "layers": [BACKGROUND, FOREGROUND],
}


class CompositeLayerSchemaTests(unittest.TestCase):
    def test_valid_background_layer_has_no_errors(self):
        self.assertEqual(validate_composite_layer_schema(BACKGROUND), [])

    def test_valid_foreground_layer_has_no_errors(self):
        self.assertEqual(validate_composite_layer_schema(FOREGROUND), [])

    def test_invalid_layer_type_is_rejected(self):
        data = dict(BACKGROUND, layer_type="midground")
        errors = validate_composite_layer_schema(data)
        self.assertTrue(any("layer_type" in e for e in errors))

    def test_chromakey_without_color_is_rejected(self):
        data = dict(FOREGROUND, chroma_color=None)
        errors = validate_composite_layer_schema(data)
        self.assertTrue(any("chroma_color" in e for e in errors))

    def test_similarity_out_of_range_is_rejected(self):
        data = dict(FOREGROUND, chroma_similarity=1.5)
        errors = validate_composite_layer_schema(data)
        self.assertTrue(any("chroma_similarity" in e for e in errors))


class CompositeResultSchemaTests(unittest.TestCase):
    def test_valid_result_has_no_errors(self):
        self.assertEqual(validate_composite_result_schema(VALID_RESULT), [])

    def test_malformed_id_is_rejected(self):
        data = dict(VALID_RESULT, id="not-a-composite-id")
        errors = validate_composite_result_schema(data)
        self.assertTrue(any("id" in e for e in errors))

    def test_missing_background_layer_is_rejected(self):
        data = dict(VALID_RESULT, layers=[FOREGROUND, FOREGROUND])
        errors = validate_composite_result_schema(data)
        self.assertTrue(any("background" in e for e in errors))

    def test_missing_foreground_layer_is_rejected(self):
        data = dict(VALID_RESULT, layers=[BACKGROUND, BACKGROUND])
        errors = validate_composite_result_schema(data)
        self.assertTrue(any("foreground" in e for e in errors))

    def test_zero_dimensions_are_rejected(self):
        data = dict(VALID_RESULT, width=0)
        errors = validate_composite_result_schema(data)
        self.assertTrue(any("width" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
