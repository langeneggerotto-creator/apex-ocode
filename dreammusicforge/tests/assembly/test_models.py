from __future__ import annotations

import unittest

from dreammusicforge.assembly.models import AssembledClip, ExportManifest, Transition

TRANSITION_DATA = {
    "source_shot_id": "SHOT-1", "destination_shot_id": "SHOT-2", "transition_type": "hard_cut",
    "duration_seconds": 0.0, "musical_anchor": "downbeat of bar 5", "visual_bridge": "none",
    "semantic_purpose": "deliberate scene change between chapters",
}
CLIP_DATA = {
    "candidate_id": "CANDIDATE-1", "shot_id": "SHOT-1", "source_hash": "a" * 64,
    "start_seconds_in_final": 0.0, "normalized_duration_seconds": 3.0,
}
MANIFEST_DATA = {
    "id": "EXPORT-deadbeef", "master_song_id": "AUDIO-deadbeef", "master_song_hash": "b" * 64,
    "output_file": "final.mp4", "output_hash": "c" * 64, "total_duration_seconds": 7.0,
    "created_at": "2026-08-05T00:00:00+00:00", "clips": [CLIP_DATA], "transitions": [TRANSITION_DATA],
}


class TransitionRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        transition = Transition.from_dict(TRANSITION_DATA)
        self.assertEqual(transition.to_dict(), TRANSITION_DATA)

    def test_transition_is_frozen(self):
        transition = Transition.from_dict(TRANSITION_DATA)
        with self.assertRaises(Exception):
            transition.transition_type = "dissolve"  # type: ignore[misc]


class AssembledClipRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        clip = AssembledClip.from_dict(CLIP_DATA)
        self.assertEqual(clip.to_dict(), CLIP_DATA)


class ExportManifestRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        manifest = ExportManifest.from_dict(MANIFEST_DATA)
        self.assertEqual(manifest.to_dict(), MANIFEST_DATA)

    def test_missing_transitions_defaults_to_empty_tuple(self):
        data = {k: v for k, v in MANIFEST_DATA.items() if k != "transitions"}
        manifest = ExportManifest.from_dict(data)
        self.assertEqual(manifest.transitions, ())

    def test_manifest_is_frozen(self):
        manifest = ExportManifest.from_dict(MANIFEST_DATA)
        with self.assertRaises(Exception):
            manifest.output_hash = "0" * 64  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
