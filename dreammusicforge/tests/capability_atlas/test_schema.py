from __future__ import annotations

import copy
import unittest

from dreammusicforge.capability_atlas.schema import validate_capability_profile_schema, validate_capability_schema

VALID_CAPABILITY = {"name": "lip_sync", "status": "measured", "evidence": "benchmarked on 40 clips"}

VALID_PROFILE = {
    "provider": "kling",
    "max_duration_seconds": 15.0,
    "max_character_count": 3,
    "supported_camera_motions": ["slow_push", "static"],
    "capabilities": [VALID_CAPABILITY, {"name": "identity", "status": "verified"}],
}


class CapabilitySchemaTests(unittest.TestCase):
    def test_valid_capability_has_no_errors(self):
        self.assertEqual(validate_capability_schema(VALID_CAPABILITY), [])

    def test_non_dict_is_rejected(self):
        self.assertTrue(validate_capability_schema(["not", "a", "dict"]))

    def test_missing_name_is_reported(self):
        data = copy.deepcopy(VALID_CAPABILITY)
        del data["name"]
        errors = validate_capability_schema(data)
        self.assertTrue(any("name" in e for e in errors))

    def test_invalid_status_is_rejected(self):
        data = dict(VALID_CAPABILITY, status="probably")
        errors = validate_capability_schema(data)
        self.assertTrue(any("status" in e for e in errors))

    def test_evidence_may_be_omitted(self):
        data = {k: v for k, v in VALID_CAPABILITY.items() if k != "evidence"}
        self.assertEqual(validate_capability_schema(data), [])

    def test_empty_evidence_is_rejected(self):
        data = dict(VALID_CAPABILITY, evidence="")
        errors = validate_capability_schema(data)
        self.assertTrue(any("evidence" in e for e in errors))

    def test_null_evidence_is_accepted(self):
        data = dict(VALID_CAPABILITY, evidence=None)
        self.assertEqual(validate_capability_schema(data), [])

    def test_every_status_is_accepted(self):
        for status in ("verified", "measured", "assumed", "unsupported", "unknown"):
            with self.subTest(status=status):
                self.assertEqual(validate_capability_schema(dict(VALID_CAPABILITY, status=status)), [])


class CapabilityProfileSchemaTests(unittest.TestCase):
    def test_valid_profile_has_no_errors(self):
        self.assertEqual(validate_capability_profile_schema(VALID_PROFILE), [])

    def test_missing_provider_is_reported(self):
        data = copy.deepcopy(VALID_PROFILE)
        del data["provider"]
        errors = validate_capability_profile_schema(data)
        self.assertTrue(any("provider" in e for e in errors))

    def test_zero_max_duration_is_rejected(self):
        data = dict(VALID_PROFILE, max_duration_seconds=0)
        errors = validate_capability_profile_schema(data)
        self.assertTrue(any("max_duration_seconds" in e for e in errors))

    def test_zero_max_character_count_is_rejected(self):
        data = dict(VALID_PROFILE, max_character_count=0)
        errors = validate_capability_profile_schema(data)
        self.assertTrue(any("max_character_count" in e for e in errors))

    def test_bool_is_rejected_for_max_character_count(self):
        data = dict(VALID_PROFILE, max_character_count=True)
        errors = validate_capability_profile_schema(data)
        self.assertTrue(any("max_character_count" in e for e in errors))

    def test_empty_supported_camera_motions_is_rejected(self):
        data = dict(VALID_PROFILE, supported_camera_motions=[])
        errors = validate_capability_profile_schema(data)
        self.assertTrue(any("supported_camera_motions" in e for e in errors))

    def test_capabilities_may_be_omitted(self):
        data = {k: v for k, v in VALID_PROFILE.items() if k != "capabilities"}
        self.assertEqual(validate_capability_profile_schema(data), [])

    def test_duplicate_capability_names_are_rejected(self):
        data = dict(VALID_PROFILE, capabilities=[VALID_CAPABILITY, dict(VALID_CAPABILITY)])
        errors = validate_capability_profile_schema(data)
        self.assertTrue(any("duplicated" in e for e in errors))

    def test_invalid_nested_capability_is_reported_with_index(self):
        data = dict(VALID_PROFILE, capabilities=[{"name": "", "status": "verified"}])
        errors = validate_capability_profile_schema(data)
        self.assertTrue(any(e.startswith("capabilities[0]") for e in errors))


if __name__ == "__main__":
    unittest.main()
