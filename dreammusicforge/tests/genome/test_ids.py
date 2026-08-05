from __future__ import annotations

import unittest

from dreammusicforge.genome.ids import (
    generate_costume_id, generate_genome_id, generate_performer_id, generate_world_id,
    is_valid_costume_id, is_valid_genome_id, is_valid_performer_id, is_valid_world_id,
)


class GenerateIdTests(unittest.TestCase):
    def test_performer_id_has_expected_prefix(self):
        self.assertTrue(generate_performer_id().startswith("PERFORMER-"))

    def test_costume_id_has_expected_prefix(self):
        self.assertTrue(generate_costume_id().startswith("COSTUME-"))

    def test_world_id_has_expected_prefix(self):
        self.assertTrue(generate_world_id().startswith("WORLD-"))

    def test_genome_id_has_expected_prefix(self):
        self.assertTrue(generate_genome_id().startswith("GENOME-"))

    def test_generated_ids_are_unique(self):
        ids = {generate_performer_id() for _ in range(200)}
        self.assertEqual(len(ids), 200)


class IsValidIdTests(unittest.TestCase):
    def test_generated_performer_id_is_valid(self):
        self.assertTrue(is_valid_performer_id(generate_performer_id()))

    def test_generated_costume_id_is_valid(self):
        self.assertTrue(is_valid_costume_id(generate_costume_id()))

    def test_generated_world_id_is_valid(self):
        self.assertTrue(is_valid_world_id(generate_world_id()))

    def test_generated_genome_id_is_valid(self):
        self.assertTrue(is_valid_genome_id(generate_genome_id()))

    def test_wrong_prefix_is_invalid(self):
        self.assertFalse(is_valid_performer_id(generate_costume_id()))

    def test_non_string_is_invalid_not_raising(self):
        self.assertFalse(is_valid_performer_id(None))  # type: ignore[arg-type]
        self.assertFalse(is_valid_costume_id(12345))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
