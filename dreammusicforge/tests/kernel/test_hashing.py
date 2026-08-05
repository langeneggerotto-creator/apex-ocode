from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.core.hashing import hash_bytes, hash_file, hash_text


class HashingTests(unittest.TestCase):
    def test_hash_bytes_is_deterministic(self):
        self.assertEqual(hash_bytes(b"hello"), hash_bytes(b"hello"))

    def test_hash_bytes_differs_for_different_input(self):
        self.assertNotEqual(hash_bytes(b"hello"), hash_bytes(b"world"))

    def test_hash_text_matches_hash_bytes_of_utf8_encoding(self):
        self.assertEqual(hash_text("hello"), hash_bytes("hello".encode("utf-8")))

    def test_hash_is_a_64_char_hex_sha256_digest(self):
        digest = hash_bytes(b"anything")
        self.assertEqual(len(digest), 64)
        int(digest, 16)  # raises ValueError if not valid hex

    def test_hash_file_matches_hash_bytes_of_its_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_bytes(b"content for hashing")
            self.assertEqual(hash_file(path), hash_bytes(b"content for hashing"))

    def test_hash_file_handles_content_larger_than_one_chunk(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large.bin"
            data = b"x" * (1024 * 1024 + 137)  # > default 1 MiB chunk size
            path.write_bytes(data)
            self.assertEqual(hash_file(path), hash_bytes(data))


if __name__ == "__main__":
    unittest.main()
