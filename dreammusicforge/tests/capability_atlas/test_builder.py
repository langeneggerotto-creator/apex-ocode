from __future__ import annotations

import unittest

from dreammusicforge.capability_atlas.builder import build_capability, build_capability_profile
from dreammusicforge.capability_atlas.errors import CapabilityAtlasValidationError


class BuildCapabilityTests(unittest.TestCase):
    def test_builds_a_valid_capability(self):
        capability = build_capability("lip_sync", "measured", evidence="benchmarked on 40 clips")
        self.assertEqual(capability.name, "lip_sync")
        self.assertEqual(capability.status, "measured")
        self.assertEqual(capability.evidence, "benchmarked on 40 clips")

    def test_evidence_defaults_to_none(self):
        capability = build_capability("lip_sync", "verified")
        self.assertIsNone(capability.evidence)

    def test_invalid_status_raises(self):
        with self.assertRaises(CapabilityAtlasValidationError):
            build_capability("lip_sync", "probably")


class BuildCapabilityProfileTests(unittest.TestCase):
    def test_builds_a_valid_profile(self):
        profile = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=3,
            supported_camera_motions=("slow_push", "static"),
            capabilities=(build_capability("identity", "verified"),),
        )
        self.assertEqual(profile.provider, "kling")
        self.assertEqual(profile.capabilities[0].name, "identity")

    def test_empty_camera_motions_raises(self):
        with self.assertRaises(CapabilityAtlasValidationError):
            build_capability_profile(provider="kling", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=())

    def test_zero_max_duration_raises(self):
        with self.assertRaises(CapabilityAtlasValidationError):
            build_capability_profile(provider="kling", max_duration_seconds=0, max_character_count=3, supported_camera_motions=("slow_push",))

    def test_duplicate_capability_names_raise(self):
        with self.assertRaises(CapabilityAtlasValidationError):
            build_capability_profile(
                provider="kling", max_duration_seconds=15.0, max_character_count=3,
                supported_camera_motions=("slow_push",),
                capabilities=(build_capability("identity", "verified"), build_capability("identity", "assumed")),
            )


if __name__ == "__main__":
    unittest.main()
