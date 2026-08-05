from __future__ import annotations

import unittest

from dreammusicforge.providers.kling.models import KLING_MODES, KlingPackage, KlingProfile

PROFILE_DATA = {"max_duration_seconds": 15.0, "supported_modes": ["image_to_video", "video_extension"]}

PACKAGE_DATA = {
    "id": "KLING-deadbeef", "render_task_id": "RENDER-deadbeef", "shot_id": "SHOT-deadbeef",
    "mode": "image_to_video", "duration_seconds": 6.5, "duration_limit_seconds": 15.0,
    "prompt": "Create 6.5 seconds of cinematic video.\n",
    "negative_prompt": ["identity drift", "wardrobe redesign"],
    "reference_manifest": ["face_front.png", "COSTUME-deadbeef"],
}


class KlingProfileRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        profile = KlingProfile.from_dict(PROFILE_DATA)
        self.assertEqual(profile.to_dict(), PROFILE_DATA)

    def test_missing_supported_modes_defaults_to_all_kling_modes(self):
        data = {k: v for k, v in PROFILE_DATA.items() if k != "supported_modes"}
        profile = KlingProfile.from_dict(data)
        self.assertEqual(profile.supported_modes, KLING_MODES)

    def test_profile_is_frozen(self):
        profile = KlingProfile.from_dict(PROFILE_DATA)
        with self.assertRaises(Exception):
            profile.max_duration_seconds = 99.0  # type: ignore[misc]


class KlingPackageRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        package = KlingPackage.from_dict(PACKAGE_DATA)
        self.assertEqual(package.to_dict(), PACKAGE_DATA)

    def test_package_is_frozen(self):
        package = KlingPackage.from_dict(PACKAGE_DATA)
        with self.assertRaises(Exception):
            package.mode = "video_extension"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
