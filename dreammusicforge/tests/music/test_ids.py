from __future__ import annotations

import unittest

from dreammusicforge.music.ids import (
    generate_audio_id, generate_lyric_id, generate_section_id, is_valid_audio_id,
    is_valid_lyric_id, is_valid_section_id,
)


class GenerateIdTests(unittest.TestCase):
    def test_audio_id_has_expected_prefix(self):
        self.assertTrue(generate_audio_id().startswith("AUDIO-"))

    def test_section_id_has_expected_prefix(self):
        self.assertTrue(generate_section_id().startswith("SECTION-"))

    def test_lyric_id_has_expected_prefix(self):
        self.assertTrue(generate_lyric_id().startswith("LYRIC-"))

    def test_generated_ids_are_unique(self):
        ids = {generate_audio_id() for _ in range(200)}
        self.assertEqual(len(ids), 200)


class IsValidIdTests(unittest.TestCase):
    def test_generated_audio_id_is_valid(self):
        self.assertTrue(is_valid_audio_id(generate_audio_id()))

    def test_generated_section_id_is_valid(self):
        self.assertTrue(is_valid_section_id(generate_section_id()))

    def test_generated_lyric_id_is_valid(self):
        self.assertTrue(is_valid_lyric_id(generate_lyric_id()))

    def test_wrong_prefix_is_invalid(self):
        self.assertFalse(is_valid_audio_id(generate_section_id()))

    def test_non_string_is_invalid_not_raising(self):
        self.assertFalse(is_valid_audio_id(None))  # type: ignore[arg-type]
        self.assertFalse(is_valid_section_id(12345))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
