from __future__ import annotations

import unittest

from dreammusicforge.providers.runway.models import RunwayPackage, RunwayProfile

PROFILE_DATA = {
    "model": "gen4_turbo", "max_duration_seconds": 10.0,
    "supported_modes": ["text_to_video", "image_to_video"],
    "supported_durations_seconds": [5.0, 10.0], "supported_ratios": ["1280:720", "720:1280"],
}

PACKAGE_DATA = {
    "id": "RUNWAY-deadbeef", "render_task_id": "RENDER-deadbeef", "shot_id": "SHOT-deadbeef",
    "mode": "image_to_video", "model": "gen4_turbo", "prompt_text": "animate this", "duration_seconds": 5.0,
    "ratio": "1280:720", "prompt_image": "https://example.com/ref.png", "seed": 7,
    "reference_manifest": ["PERFORMER-deadbeef", "COSTUME-deadbeef", "WORLD-deadbeef"],
}


class RunwayProfileRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        profile = RunwayProfile.from_dict(PROFILE_DATA)
        self.assertEqual(profile.to_dict(), PROFILE_DATA)

    def test_defaults_when_optional_fields_omitted(self):
        profile = RunwayProfile.from_dict({"model": "gen4_turbo"})
        self.assertEqual(profile.max_duration_seconds, 10.0)
        self.assertIn("image_to_video", profile.supported_modes)


class RunwayPackageRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        package = RunwayPackage.from_dict(PACKAGE_DATA)
        self.assertEqual(package.to_dict(), PACKAGE_DATA)

    def test_package_is_frozen(self):
        package = RunwayPackage.from_dict(PACKAGE_DATA)
        with self.assertRaises(AttributeError):
            package.duration_seconds = 20.0

    def test_missing_optional_fields_default_to_none_and_empty(self):
        data = {k: v for k, v in PACKAGE_DATA.items() if k not in ("prompt_image", "seed", "reference_manifest")}
        package = RunwayPackage.from_dict(data)
        self.assertIsNone(package.prompt_image)
        self.assertIsNone(package.seed)
        self.assertEqual(package.reference_manifest, ())


if __name__ == "__main__":
    unittest.main()
