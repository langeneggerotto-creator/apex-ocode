from __future__ import annotations

import unittest

from dreammusicforge.generation.models import Candidate

CANDIDATE_DATA = {
    "id": "CANDIDATE-deadbeef",
    "render_task_id": "RENDER-021-B",
    "provider": "kling",
    "model_version": "kling-v1.6",
    "file": "renders/CANDIDATE-021-B-003.mp4",
    "file_size_bytes": 4_200_000,
    "prompt_hash": "a" * 64,
    "reference_hashes": ["b" * 64, "c" * 64],
    "output_hash": "d" * 64,
    "imported_at": "2026-08-05T12:00:00+00:00",
    "verification_status": "pending",
    "decision": "pending",
}


class CandidateRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        candidate = Candidate.from_dict(CANDIDATE_DATA)
        self.assertEqual(candidate.to_dict(), CANDIDATE_DATA)

    def test_missing_reference_hashes_defaults_to_empty_tuple(self):
        data = {k: v for k, v in CANDIDATE_DATA.items() if k != "reference_hashes"}
        candidate = Candidate.from_dict(data)
        self.assertEqual(candidate.reference_hashes, ())

    def test_missing_verification_status_defaults_to_pending(self):
        data = {k: v for k, v in CANDIDATE_DATA.items() if k != "verification_status"}
        candidate = Candidate.from_dict(data)
        self.assertEqual(candidate.verification_status, "pending")

    def test_missing_decision_defaults_to_pending(self):
        data = {k: v for k, v in CANDIDATE_DATA.items() if k != "decision"}
        candidate = Candidate.from_dict(data)
        self.assertEqual(candidate.decision, "pending")

    def test_candidate_is_frozen(self):
        candidate = Candidate.from_dict(CANDIDATE_DATA)
        with self.assertRaises(Exception):
            candidate.decision = "accept"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
