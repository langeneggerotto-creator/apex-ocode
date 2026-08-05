from __future__ import annotations

import unittest

from dreammusicforge.generation.ids import generate_candidate_id, is_valid_candidate_id


class GenerateCandidateIdTests(unittest.TestCase):
    def test_generated_id_has_expected_prefix(self):
        self.assertTrue(generate_candidate_id().startswith("CANDIDATE-"))

    def test_generated_id_is_valid(self):
        self.assertTrue(is_valid_candidate_id(generate_candidate_id()))

    def test_generated_ids_are_unique(self):
        ids = {generate_candidate_id() for _ in range(200)}
        self.assertEqual(len(ids), 200)

    def test_non_string_is_invalid_not_raising(self):
        self.assertFalse(is_valid_candidate_id(None))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
