from __future__ import annotations

import unittest

from dreammusicforge.production.ids import (
    generate_graph_id, generate_semantic_event_id, generate_sequence_id, generate_shot_id,
    is_valid_graph_id, is_valid_semantic_event_id, is_valid_sequence_id, is_valid_shot_id,
)


class GenerateIdTests(unittest.TestCase):
    def test_sequence_id_has_expected_prefix(self):
        self.assertTrue(generate_sequence_id().startswith("SEQ-"))

    def test_semantic_event_id_has_expected_prefix(self):
        self.assertTrue(generate_semantic_event_id().startswith("SEM-"))

    def test_shot_id_has_expected_prefix(self):
        self.assertTrue(generate_shot_id().startswith("SHOT-"))

    def test_graph_id_has_expected_prefix(self):
        self.assertTrue(generate_graph_id().startswith("GRAPH-"))

    def test_generated_ids_are_unique(self):
        ids = {generate_shot_id() for _ in range(200)}
        self.assertEqual(len(ids), 200)


class IsValidIdTests(unittest.TestCase):
    def test_generated_sequence_id_is_valid(self):
        self.assertTrue(is_valid_sequence_id(generate_sequence_id()))

    def test_generated_semantic_event_id_is_valid(self):
        self.assertTrue(is_valid_semantic_event_id(generate_semantic_event_id()))

    def test_generated_shot_id_is_valid(self):
        self.assertTrue(is_valid_shot_id(generate_shot_id()))

    def test_generated_graph_id_is_valid(self):
        self.assertTrue(is_valid_graph_id(generate_graph_id()))

    def test_wrong_prefix_is_invalid(self):
        self.assertFalse(is_valid_sequence_id(generate_shot_id()))

    def test_non_string_is_invalid_not_raising(self):
        self.assertFalse(is_valid_shot_id(None))  # type: ignore[arg-type]
        self.assertFalse(is_valid_sequence_id(12345))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
