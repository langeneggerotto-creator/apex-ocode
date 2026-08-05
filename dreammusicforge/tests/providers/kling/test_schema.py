from __future__ import annotations

import copy
import unittest

from dreammusicforge.providers.kling.schema import validate_kling_package_schema, validate_kling_profile_schema

VALID_PROFILE = {"max_duration_seconds": 15.0, "supported_modes": ["image_to_video", "video_extension"]}

VALID_PACKAGE = {
    "id": "KLING-deadbeef", "render_task_id": "RENDER-deadbeef", "shot_id": "SHOT-deadbeef",
    "mode": "image_to_video", "duration_seconds": 6.5, "duration_limit_seconds": 15.0,
    "prompt": "Create 6.5 seconds of cinematic video.\n",
    "negative_prompt": ["identity drift"], "reference_manifest": ["face_front.png"],
}


class KlingProfileSchemaTests(unittest.TestCase):
    def test_valid_profile_has_no_errors(self):
        self.assertEqual(validate_kling_profile_schema(VALID_PROFILE), [])

    def test_zero_max_duration_is_rejected(self):
        data = dict(VALID_PROFILE, max_duration_seconds=0)
        errors = validate_kling_profile_schema(data)
        self.assertTrue(any("max_duration_seconds" in e for e in errors))

    def test_supported_modes_may_be_omitted(self):
        data = {k: v for k, v in VALID_PROFILE.items() if k != "supported_modes"}
        self.assertEqual(validate_kling_profile_schema(data), [])

    def test_unknown_mode_is_rejected(self):
        data = dict(VALID_PROFILE, supported_modes=["teleport"])
        errors = validate_kling_profile_schema(data)
        self.assertTrue(any("unknown modes" in e for e in errors))

    def test_empty_supported_modes_is_rejected(self):
        data = dict(VALID_PROFILE, supported_modes=[])
        errors = validate_kling_profile_schema(data)
        self.assertTrue(any("supported_modes" in e for e in errors))


class KlingPackageSchemaTests(unittest.TestCase):
    def test_valid_package_has_no_errors(self):
        self.assertEqual(validate_kling_package_schema(VALID_PACKAGE), [])

    def test_malformed_id_is_rejected(self):
        data = dict(VALID_PACKAGE, id="not-a-kling-id")
        errors = validate_kling_package_schema(data)
        self.assertTrue(any("id" in e for e in errors))

    def test_invalid_mode_is_rejected(self):
        data = dict(VALID_PACKAGE, mode="teleport")
        errors = validate_kling_package_schema(data)
        self.assertTrue(any("mode" in e for e in errors))

    def test_duration_exceeding_limit_is_rejected(self):
        data = dict(VALID_PACKAGE, duration_seconds=20.0, duration_limit_seconds=15.0)
        errors = validate_kling_package_schema(data)
        self.assertTrue(any("exceeds" in e for e in errors))

    def test_empty_negative_prompt_is_rejected(self):
        data = dict(VALID_PACKAGE, negative_prompt=[])
        errors = validate_kling_package_schema(data)
        self.assertTrue(any("negative_prompt" in e for e in errors))

    def test_empty_reference_manifest_is_rejected(self):
        data = dict(VALID_PACKAGE, reference_manifest=[])
        errors = validate_kling_package_schema(data)
        self.assertTrue(any("reference_manifest" in e for e in errors))

    def test_missing_prompt_is_reported(self):
        data = copy.deepcopy(VALID_PACKAGE)
        del data["prompt"]
        errors = validate_kling_package_schema(data)
        self.assertTrue(any("prompt" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
