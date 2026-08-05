from __future__ import annotations

import copy
import unittest

from dreammusicforge.generation.schema import validate_candidate_schema

VALID_CANDIDATE = {
    "id": "CANDIDATE-deadbeef",
    "render_task_id": "RENDER-021-B",
    "provider": "kling",
    "model_version": "kling-v1.6",
    "file": "renders/CANDIDATE-021-B-003.mp4",
    "file_size_bytes": 4_200_000,
    "prompt_hash": "a" * 64,
    "output_hash": "d" * 64,
    "imported_at": "2026-08-05T12:00:00+00:00",
}


class CandidateSchemaTests(unittest.TestCase):
    def test_valid_candidate_has_no_errors(self):
        self.assertEqual(validate_candidate_schema(VALID_CANDIDATE), [])

    def test_non_dict_is_rejected(self):
        self.assertTrue(validate_candidate_schema(["not", "a", "dict"]))

    def test_malformed_id_is_rejected(self):
        data = dict(VALID_CANDIDATE, id="not-a-candidate-id")
        errors = validate_candidate_schema(data)
        self.assertTrue(any("id" in e for e in errors))

    def test_missing_render_task_id_is_reported(self):
        data = copy.deepcopy(VALID_CANDIDATE)
        del data["render_task_id"]
        errors = validate_candidate_schema(data)
        self.assertTrue(any("render_task_id" in e for e in errors))

    def test_zero_file_size_is_rejected(self):
        data = dict(VALID_CANDIDATE, file_size_bytes=0)
        errors = validate_candidate_schema(data)
        self.assertTrue(any("file_size_bytes" in e for e in errors))

    def test_negative_file_size_is_rejected(self):
        data = dict(VALID_CANDIDATE, file_size_bytes=-1)
        errors = validate_candidate_schema(data)
        self.assertTrue(any("file_size_bytes" in e for e in errors))

    def test_short_prompt_hash_is_rejected(self):
        data = dict(VALID_CANDIDATE, prompt_hash="abc123")
        errors = validate_candidate_schema(data)
        self.assertTrue(any("prompt_hash" in e for e in errors))

    def test_uppercase_hash_is_rejected(self):
        data = dict(VALID_CANDIDATE, output_hash="D" * 64)
        errors = validate_candidate_schema(data)
        self.assertTrue(any("output_hash" in e for e in errors))

    def test_non_hex_hash_is_rejected(self):
        data = dict(VALID_CANDIDATE, output_hash="g" * 64)
        errors = validate_candidate_schema(data)
        self.assertTrue(any("output_hash" in e for e in errors))

    def test_reference_hashes_may_be_omitted(self):
        self.assertEqual(validate_candidate_schema(VALID_CANDIDATE), [])

    def test_malformed_reference_hash_is_rejected(self):
        data = dict(VALID_CANDIDATE, reference_hashes=["not-a-hash"])
        errors = validate_candidate_schema(data)
        self.assertTrue(any("reference_hashes" in e for e in errors))

    def test_invalid_verification_status_is_rejected(self):
        data = dict(VALID_CANDIDATE, verification_status="maybe")
        errors = validate_candidate_schema(data)
        self.assertTrue(any("verification_status" in e for e in errors))

    def test_invalid_decision_is_rejected(self):
        data = dict(VALID_CANDIDATE, decision="undecided")
        errors = validate_candidate_schema(data)
        self.assertTrue(any("decision" in e for e in errors))

    def test_verification_status_and_decision_may_be_omitted(self):
        self.assertEqual(validate_candidate_schema(VALID_CANDIDATE), [])


if __name__ == "__main__":
    unittest.main()
