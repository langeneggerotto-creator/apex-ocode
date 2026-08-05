from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.core.errors import PathConfinementError
from dreammusicforge.core.paths import confine_path


class ConfinePathTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_simple_relative_path_is_allowed(self):
        result = confine_path(self.root, "project.json")
        self.assertEqual(result, (self.root / "project.json").resolve())

    def test_nested_relative_path_is_allowed(self):
        result = confine_path(self.root, "subdir/nested/file.json")
        self.assertEqual(result, (self.root / "subdir" / "nested" / "file.json").resolve())

    def test_dotdot_traversal_is_blocked(self):
        with self.assertRaises(PathConfinementError):
            confine_path(self.root, "../../etc/passwd")

    def test_absolute_path_escape_is_blocked(self):
        with self.assertRaises(PathConfinementError):
            confine_path(self.root, "/etc/passwd")

    def test_dotdot_that_stays_inside_root_is_allowed(self):
        # subdir/../project.json resolves back to root/project.json -- still inside root.
        result = confine_path(self.root, "subdir/../project.json")
        self.assertEqual(result, (self.root / "project.json").resolve())

    def test_symlink_escape_is_blocked(self):
        outside = tempfile.TemporaryDirectory()
        try:
            secret = Path(outside.name) / "secret.txt"
            secret.write_text("outside the workspace")
            link = self.root / "escape_link"
            link.symlink_to(secret)
            with self.assertRaises(PathConfinementError):
                confine_path(self.root, "escape_link")
        finally:
            outside.cleanup()

    def test_nonexistent_root_is_rejected(self):
        with self.assertRaises(PathConfinementError):
            confine_path(self.root / "does_not_exist", "file.json")


if __name__ == "__main__":
    unittest.main()
