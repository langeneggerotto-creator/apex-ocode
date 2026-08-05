from __future__ import annotations

import unittest

from dreammusicforge.core.errors import InvalidProjectIdError
from dreammusicforge.core.ids import generate_project_id, is_valid_project_id, validate_project_id


class GenerateProjectIdTests(unittest.TestCase):
    def test_generated_id_has_expected_prefix(self):
        self.assertTrue(generate_project_id().startswith("DMF-PROJECT-"))

    def test_generated_id_is_valid(self):
        self.assertTrue(is_valid_project_id(generate_project_id()))

    def test_generated_ids_are_unique(self):
        ids = {generate_project_id() for _ in range(200)}
        self.assertEqual(len(ids), 200, "generated ids should not collide across 200 calls")


class ValidateProjectIdTests(unittest.TestCase):
    def test_valid_id_does_not_raise(self):
        validate_project_id(generate_project_id())  # should not raise

    def test_malformed_id_raises(self):
        with self.assertRaises(InvalidProjectIdError):
            validate_project_id("not-an-id")

    def test_wrong_prefix_raises(self):
        with self.assertRaises(InvalidProjectIdError):
            validate_project_id("PROJECT-deadbeef")

    def test_short_hex_suffix_raises(self):
        with self.assertRaises(InvalidProjectIdError):
            validate_project_id("DMF-PROJECT-abc")

    def test_uppercase_hex_raises(self):
        with self.assertRaises(InvalidProjectIdError):
            validate_project_id("DMF-PROJECT-DEADBEEF")

    def test_non_string_raises(self):
        with self.assertRaises(InvalidProjectIdError):
            validate_project_id(12345)  # type: ignore[arg-type]


class IsValidProjectIdTests(unittest.TestCase):
    def test_returns_false_not_raises_for_bad_input(self):
        self.assertFalse(is_valid_project_id("garbage"))
        self.assertFalse(is_valid_project_id(None))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
