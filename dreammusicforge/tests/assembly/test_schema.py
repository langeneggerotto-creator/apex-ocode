from __future__ import annotations

import copy
import unittest

from dreammusicforge.assembly.schema import (
    validate_assembled_clip_schema, validate_export_manifest_schema, validate_transition_schema,
)

VALID_TRANSITION = {
    "source_shot_id": "SHOT-1", "destination_shot_id": "SHOT-2", "transition_type": "hard_cut",
    "duration_seconds": 0.0, "musical_anchor": "downbeat", "visual_bridge": "none", "semantic_purpose": "scene change",
}
VALID_CLIP = {
    "candidate_id": "CANDIDATE-1", "shot_id": "SHOT-1", "source_hash": "a" * 64,
    "start_seconds_in_final": 0.0, "normalized_duration_seconds": 3.0,
}
VALID_CLIP_2 = dict(VALID_CLIP, candidate_id="CANDIDATE-2", shot_id="SHOT-2", start_seconds_in_final=3.0)
VALID_MANIFEST = {
    "id": "EXPORT-deadbeef", "master_song_id": "AUDIO-deadbeef", "master_song_hash": "b" * 64,
    "output_file": "final.mp4", "output_hash": "c" * 64, "total_duration_seconds": 7.0,
    "created_at": "2026-08-05T00:00:00+00:00", "clips": [VALID_CLIP, VALID_CLIP_2],
}


class TransitionSchemaTests(unittest.TestCase):
    def test_valid_transition_has_no_errors(self):
        self.assertEqual(validate_transition_schema(VALID_TRANSITION), [])

    def test_invalid_transition_type_is_rejected(self):
        data = dict(VALID_TRANSITION, transition_type="teleport")
        errors = validate_transition_schema(data)
        self.assertTrue(any("transition_type" in e for e in errors))

    def test_negative_duration_is_rejected(self):
        data = dict(VALID_TRANSITION, duration_seconds=-1.0)
        errors = validate_transition_schema(data)
        self.assertTrue(any("duration_seconds" in e for e in errors))

    def test_every_spec_transition_type_is_accepted(self):
        for transition_type in (
            "hard_cut", "dissolve", "dip_to_black", "foreground_wipe", "motion_match",
            "graphic_match", "color_bridge", "light_flash", "blur_transition", "beat_cut",
        ):
            with self.subTest(transition_type=transition_type):
                self.assertEqual(validate_transition_schema(dict(VALID_TRANSITION, transition_type=transition_type)), [])


class AssembledClipSchemaTests(unittest.TestCase):
    def test_valid_clip_has_no_errors(self):
        self.assertEqual(validate_assembled_clip_schema(VALID_CLIP), [])

    def test_malformed_hash_is_rejected(self):
        data = dict(VALID_CLIP, source_hash="not-a-hash")
        errors = validate_assembled_clip_schema(data)
        self.assertTrue(any("source_hash" in e for e in errors))

    def test_zero_duration_is_rejected(self):
        data = dict(VALID_CLIP, normalized_duration_seconds=0)
        errors = validate_assembled_clip_schema(data)
        self.assertTrue(any("normalized_duration_seconds" in e for e in errors))


class ExportManifestSchemaTests(unittest.TestCase):
    def test_valid_manifest_has_no_errors(self):
        self.assertEqual(validate_export_manifest_schema(VALID_MANIFEST), [])

    def test_malformed_id_is_rejected(self):
        data = dict(VALID_MANIFEST, id="not-an-export-id")
        errors = validate_export_manifest_schema(data)
        self.assertTrue(any("id" in e for e in errors))

    def test_empty_clips_is_rejected(self):
        data = dict(VALID_MANIFEST, clips=[])
        errors = validate_export_manifest_schema(data)
        self.assertTrue(any("clips" in e for e in errors))

    def test_overlapping_clips_are_rejected(self):
        data = copy.deepcopy(VALID_MANIFEST)
        data["clips"][1]["start_seconds_in_final"] = 1.0  # overlaps clip 1's 0.0-3.0
        errors = validate_export_manifest_schema(data)
        self.assertTrue(any("overlap" in e for e in errors))

    def test_adjacent_non_overlapping_clips_are_accepted(self):
        self.assertEqual(validate_export_manifest_schema(VALID_MANIFEST), [])

    def test_invalid_nested_transition_is_reported(self):
        data = dict(VALID_MANIFEST, transitions=[dict(VALID_TRANSITION, transition_type="teleport")])
        errors = validate_export_manifest_schema(data)
        self.assertTrue(any(e.startswith("transitions[0]") for e in errors))

    def test_malformed_master_song_hash_is_rejected(self):
        data = dict(VALID_MANIFEST, master_song_hash="short")
        errors = validate_export_manifest_schema(data)
        self.assertTrue(any("master_song_hash" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
