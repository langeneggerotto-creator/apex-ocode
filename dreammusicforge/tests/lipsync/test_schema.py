from __future__ import annotations

import unittest

from dreammusicforge.lipsync.schema import validate_lip_sync_request_schema, validate_lip_sync_result_schema

VALID_REQUEST = {
    "id": "LIPSYNC-deadbeef", "shot_id": "SHOT-deadbeef", "candidate_id": "CANDIDATE-deadbeef",
    "source_file": "clip.mp4", "audio_window_file": "window.wav",
    "audio_start_seconds": 10.0, "audio_end_seconds": 15.0,
}

VALID_RESULT = {
    "request_id": "LIPSYNC-deadbeef", "status": "not_applied",
    "reason": "no lip-sync engine is integrated in this release", "output_file": None,
}


class LipSyncRequestSchemaTests(unittest.TestCase):
    def test_valid_request_has_no_errors(self):
        self.assertEqual(validate_lip_sync_request_schema(VALID_REQUEST), [])

    def test_malformed_id_is_rejected(self):
        data = dict(VALID_REQUEST, id="not-a-lipsync-id")
        errors = validate_lip_sync_request_schema(data)
        self.assertTrue(any("id" in e for e in errors))

    def test_start_after_end_is_rejected(self):
        data = dict(VALID_REQUEST, audio_start_seconds=20.0, audio_end_seconds=15.0)
        errors = validate_lip_sync_request_schema(data)
        self.assertTrue(any("audio_start_seconds" in e for e in errors))

    def test_missing_field_is_reported(self):
        data = {k: v for k, v in VALID_REQUEST.items() if k != "candidate_id"}
        errors = validate_lip_sync_request_schema(data)
        self.assertTrue(any("candidate_id" in e for e in errors))


class LipSyncResultSchemaTests(unittest.TestCase):
    def test_valid_result_has_no_errors(self):
        self.assertEqual(validate_lip_sync_result_schema(VALID_RESULT), [])

    def test_invalid_status_is_rejected(self):
        data = dict(VALID_RESULT, status="maybe")
        errors = validate_lip_sync_result_schema(data)
        self.assertTrue(any("status" in e for e in errors))

    def test_applied_without_output_file_is_rejected(self):
        data = dict(VALID_RESULT, status="applied", output_file=None)
        errors = validate_lip_sync_result_schema(data)
        self.assertTrue(any("output_file" in e for e in errors))

    def test_applied_with_output_file_has_no_errors(self):
        data = dict(VALID_RESULT, status="applied", output_file="synced.mp4")
        self.assertEqual(validate_lip_sync_result_schema(data), [])


if __name__ == "__main__":
    unittest.main()
