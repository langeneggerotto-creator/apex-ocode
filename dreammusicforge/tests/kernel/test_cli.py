from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from dreammusicforge.apps.cli.main import main


def _run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class CliInitTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_init_succeeds_and_writes_project_json(self):
        code, out, err = _run(["project", "init", "Begin Again", "--workspace", str(self.workspace)])
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["title"], "Begin Again")
        self.assertEqual(data["status"], "draft")
        project_json = self.workspace / "project.json"
        self.assertTrue(project_json.is_file())
        self.assertEqual(json.loads(project_json.read_text())["id"], data["id"])

    def test_init_creates_the_sqlite_db(self):
        _run(["project", "init", "Begin Again", "--workspace", str(self.workspace)])
        self.assertTrue((self.workspace / ".dreammusicforge" / "kernel.db").is_file())

    def test_init_with_explicit_providers(self):
        code, out, _ = _run([
            "project", "init", "Begin Again", "--workspace", str(self.workspace),
            "--provider", "kling", "--provider", "veo",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["providers"], ["kling", "veo"])

    def test_init_with_explicit_id_uses_that_id(self):
        code, out, _ = _run([
            "project", "init", "Begin Again", "--workspace", str(self.workspace),
            "--id", "DMF-PROJECT-cafebabe",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["id"], "DMF-PROJECT-cafebabe")

    def test_init_with_malformed_explicit_id_fails_closed(self):
        code, out, err = _run([
            "project", "init", "Begin Again", "--workspace", str(self.workspace),
            "--id", "not-a-valid-id",
        ])
        self.assertEqual(code, 1)
        self.assertIn("not a valid project id", err)


class CliValidateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_validate_a_freshly_initialized_project_passes(self):
        _run(["project", "init", "Begin Again", "--workspace", str(self.workspace)])
        code, out, err = _run(["project", "validate", str(self.workspace / "project.json")])
        self.assertEqual(code, 0, err)
        self.assertIn("valid", out)

    def test_validate_missing_file_fails_closed(self):
        code, out, err = _run(["project", "validate", str(self.workspace / "nope.json")])
        self.assertEqual(code, 1)
        self.assertIn("no such file", err)

    def test_validate_malformed_json_fails_closed(self):
        bad = self.workspace / "bad.json"
        bad.write_text("{not valid json")
        code, out, err = _run(["project", "validate", str(bad)])
        self.assertEqual(code, 1)
        self.assertIn("not valid JSON", err)

    def test_validate_reports_every_missing_field(self):
        bad = self.workspace / "incomplete.json"
        bad.write_text(json.dumps({"id": "DMF-PROJECT-deadbeef"}))
        code, out, err = _run(["project", "validate", str(bad)])
        self.assertEqual(code, 1)
        self.assertGreaterEqual(err.count("error:"), 5)


class CliShowTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_show_a_project_created_by_init(self):
        _, init_out, _ = _run(["project", "init", "Begin Again", "--workspace", str(self.workspace)])
        project_id = json.loads(init_out)["id"]

        code, out, err = _run(["project", "show", project_id, "--workspace", str(self.workspace)])
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["id"], project_id)

    def test_show_missing_project_fails_closed(self):
        (self.workspace / ".dreammusicforge").mkdir()
        code, out, err = _run(["project", "show", "DMF-PROJECT-00000000", "--workspace", str(self.workspace)])
        self.assertEqual(code, 1)
        self.assertIn("no project found", err)


if __name__ == "__main__":
    unittest.main()
