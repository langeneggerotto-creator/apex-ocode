from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from dreammusicforge.runtime import compile_kling_packages, validate_project


EXAMPLE = Path(__file__).parents[1] / "examples" / "begin_again_project.json"


class DreamMusicForgeRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.project = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_valid_project(self):
        result = validate_project(self.project)
        self.assertTrue(result.valid, result.errors)

    def test_last_frame_handoff(self):
        packages = compile_kling_packages(self.project)
        self.assertIn(
            "CLIP-001-VERIFIED-END.png",
            packages[1]["required_assets"],
        )

    def test_state_inheritance_failure(self):
        project = copy.deepcopy(self.project)
        project["clips"][1]["source_state_id"] = "STATE-000"
        result = validate_project(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("breaks state inheritance" in item for item in result.errors))

    def test_duration_limit_failure(self):
        project = copy.deepcopy(self.project)
        project["clips"][0]["end"] = 16
        result = validate_project(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("duration limit" in item for item in result.errors))

    def test_action_limit_failure(self):
        project = copy.deepcopy(self.project)
        project["clips"][1]["secondary_actions"] = ["turn page"]
        result = validate_project(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("maximum action count" in item for item in result.errors))

    def test_music_is_master_clock(self):
        packages = compile_kling_packages(self.project)
        self.assertIn("The song is the master clock", packages[0]["prompt"])


if __name__ == "__main__":
    unittest.main()
