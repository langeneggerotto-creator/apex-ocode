from __future__ import annotations

import unittest

from dreammusicforge.providers.runway.schema import validate_runway_package_schema, validate_runway_profile_schema

VALID_PROFILE = {
    "model": "gen4_turbo", "max_duration_seconds": 10.0,
    "supported_modes": ["text_to_video", "image_to_video"],
    "supported_durations_seconds": [5.0, 10.0], "supported_ratios": ["1280:720"],
}

VALID_PACKAGE = {
    "id": "RUNWAY-deadbeef", "render_task_id": "RENDER-deadbeef", "shot_id": "SHOT-deadbeef",
    "mode": "image_to_video", "model": "gen4_turbo", "prompt_text": "animate this", "duration_seconds": 5.0,
    "ratio": "1280:720", "prompt_image": "https://example.com/ref.png", "negative_prompt": "identity drift",
    "seed": 7, "audio": True,
    "reference_manifest": ["PERFORMER-deadbeef"],
}


class RunwayProfileSchemaTests(unittest.TestCase):
    def test_valid_profile_has_no_errors(self):
        self.assertEqual(validate_runway_profile_schema(VALID_PROFILE), [])

    def test_missing_model_is_rejected(self):
        data = dict(VALID_PROFILE)
        del data["model"]
        errors = validate_runway_profile_schema(data)
        self.assertTrue(any("model" in e for e in errors))

    def test_unknown_mode_is_rejected(self):
        data = dict(VALID_PROFILE, supported_modes=["video_extension"])
        errors = validate_runway_profile_schema(data)
        self.assertTrue(any("supported_modes" in e for e in errors))


class RunwayPackageSchemaTests(unittest.TestCase):
    def test_valid_package_has_no_errors(self):
        self.assertEqual(validate_runway_package_schema(VALID_PACKAGE), [])

    def test_malformed_id_is_rejected(self):
        data = dict(VALID_PACKAGE, id="not-a-runway-id")
        errors = validate_runway_package_schema(data)
        self.assertTrue(any("id" in e for e in errors))

    def test_image_to_video_without_prompt_image_is_rejected(self):
        data = dict(VALID_PACKAGE, prompt_image=None)
        errors = validate_runway_package_schema(data)
        self.assertTrue(any("prompt_image" in e for e in errors))

    def test_text_to_video_without_prompt_image_is_valid(self):
        data = dict(VALID_PACKAGE, mode="text_to_video", prompt_image=None)
        self.assertEqual(validate_runway_package_schema(data), [])

    def test_negative_seed_is_rejected(self):
        data = dict(VALID_PACKAGE, seed=-1)
        errors = validate_runway_package_schema(data)
        self.assertTrue(any("seed" in e for e in errors))

    def test_invalid_mode_is_rejected(self):
        data = dict(VALID_PACKAGE, mode="video_extension")
        errors = validate_runway_package_schema(data)
        self.assertTrue(any("mode" in e for e in errors))

    def test_non_bool_audio_is_rejected(self):
        data = dict(VALID_PACKAGE, audio="yes")
        errors = validate_runway_package_schema(data)
        self.assertTrue(any("audio" in e for e in errors))

    def test_empty_negative_prompt_is_rejected(self):
        data = dict(VALID_PACKAGE, negative_prompt="")
        errors = validate_runway_package_schema(data)
        self.assertTrue(any("negative_prompt" in e for e in errors))

    def test_null_negative_prompt_is_valid(self):
        data = dict(VALID_PACKAGE, negative_prompt=None)
        self.assertEqual(validate_runway_package_schema(data), [])


if __name__ == "__main__":
    unittest.main()
