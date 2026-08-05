from __future__ import annotations

import unittest

from dreammusicforge.providers.kling.ids import generate_kling_package_id, is_valid_kling_package_id


class GenerateKlingPackageIdTests(unittest.TestCase):
    def test_generated_id_has_expected_prefix(self):
        self.assertTrue(generate_kling_package_id().startswith("KLING-"))

    def test_generated_id_is_valid(self):
        self.assertTrue(is_valid_kling_package_id(generate_kling_package_id()))

    def test_generated_ids_are_unique(self):
        ids = {generate_kling_package_id() for _ in range(200)}
        self.assertEqual(len(ids), 200)

    def test_non_string_is_invalid_not_raising(self):
        self.assertFalse(is_valid_kling_package_id(None))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
