from __future__ import annotations

import unittest

from dreammusicforge.lipsync.models import LipSyncRequest, LipSyncResult

REQUEST_DATA = {
    "id": "LIPSYNC-deadbeef",
    "shot_id": "SHOT-deadbeef",
    "candidate_id": "CANDIDATE-deadbeef",
    "source_file": "clip.mp4",
    "audio_window_file": "window.wav",
    "audio_start_seconds": 10.0,
    "audio_end_seconds": 15.0,
}

RESULT_DATA = {
    "request_id": "LIPSYNC-deadbeef",
    "status": "not_applied",
    "reason": "no lip-sync engine is integrated in this release",
    "output_file": None,
}


class LipSyncRequestRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        request = LipSyncRequest.from_dict(REQUEST_DATA)
        self.assertEqual(request.to_dict(), REQUEST_DATA)

    def test_request_is_frozen(self):
        request = LipSyncRequest.from_dict(REQUEST_DATA)
        with self.assertRaises(AttributeError):
            request.shot_id = "SHOT-other"


class LipSyncResultRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        result = LipSyncResult.from_dict(RESULT_DATA)
        self.assertEqual(result.to_dict(), RESULT_DATA)

    def test_missing_output_file_defaults_to_none(self):
        data = {k: v for k, v in RESULT_DATA.items() if k != "output_file"}
        result = LipSyncResult.from_dict(data)
        self.assertIsNone(result.output_file)


if __name__ == "__main__":
    unittest.main()
