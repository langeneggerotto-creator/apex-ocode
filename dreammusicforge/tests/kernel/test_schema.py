from __future__ import annotations

import copy
import unittest

from dreammusicforge.core.schema import validate_project_schema

VALID_DATA = {
    "id": "DMF-PROJECT-deadbeef",
    "title": "Begin Again",
    "version": "0.1.0",
    "status": "draft",
    "aspect_ratio": "16:9",
    "resolution": "1920x1080",
    "frame_rate": 30,
    "target_duration_seconds": 240,
    "providers": ["kling", "veo"],
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}


class ValidProjectTests(unittest.TestCase):
    def test_valid_project_has_no_errors(self):
        self.assertEqual(validate_project_schema(VALID_DATA), [])

    def test_optional_ids_may_be_omitted(self):
        self.assertEqual(validate_project_schema(VALID_DATA), [])

    def test_optional_ids_may_be_explicit_strings(self):
        data = dict(VALID_DATA, master_song_id="AUDIO-001", film_genome_id="GENOME-001")
        self.assertEqual(validate_project_schema(data), [])


class SchemaFailureTests(unittest.TestCase):
    def test_non_dict_is_rejected(self):
        errors = validate_project_schema(["not", "a", "dict"])
        self.assertTrue(errors)

    def test_missing_required_field_is_reported(self):
        data = copy.deepcopy(VALID_DATA)
        del data["title"]
        errors = validate_project_schema(data)
        self.assertTrue(any("title" in e for e in errors))

    def test_missing_multiple_fields_reports_all_of_them(self):
        data = {"id": VALID_DATA["id"]}
        errors = validate_project_schema(data)
        self.assertGreaterEqual(len(errors), 9)

    def test_invalid_status_is_rejected(self):
        data = dict(VALID_DATA, status="deleted")
        errors = validate_project_schema(data)
        self.assertTrue(any("status" in e for e in errors))

    def test_zero_frame_rate_is_rejected(self):
        data = dict(VALID_DATA, frame_rate=0)
        errors = validate_project_schema(data)
        self.assertTrue(any("frame_rate" in e for e in errors))

    def test_negative_duration_is_rejected(self):
        data = dict(VALID_DATA, target_duration_seconds=-5)
        errors = validate_project_schema(data)
        self.assertTrue(any("target_duration_seconds" in e for e in errors))

    def test_bool_is_rejected_for_numeric_frame_rate(self):
        """bool is a subclass of int in Python -- True/False must not
        silently pass a numeric check."""
        data = dict(VALID_DATA, frame_rate=True)
        errors = validate_project_schema(data)
        self.assertTrue(any("frame_rate" in e for e in errors))

    def test_providers_must_be_a_list(self):
        data = dict(VALID_DATA, providers="kling")
        errors = validate_project_schema(data)
        self.assertTrue(any("providers" in e for e in errors))

    def test_providers_must_contain_only_non_empty_strings(self):
        data = dict(VALID_DATA, providers=["kling", "", 42])
        errors = validate_project_schema(data)
        self.assertTrue(any("providers" in e for e in errors))

    def test_empty_optional_id_string_is_rejected(self):
        data = dict(VALID_DATA, master_song_id="")
        errors = validate_project_schema(data)
        self.assertTrue(any("master_song_id" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
