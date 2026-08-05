from __future__ import annotations

import copy
import unittest

from dreammusicforge.production.schema import (
    validate_production_graph_schema, validate_semantic_event_schema, validate_sequence_schema,
    validate_shot_schema,
)

VALID_SEMANTIC_EVENT = {
    "id": "SEM-deadbeef", "start_seconds": 42.0, "end_seconds": 48.5,
    "meaning": "confidence becomes declaration", "transformation_from": "uncertainty", "transformation_to": "agency",
}

VALID_SEQUENCE = {"id": "SEQ-deadbeef", "song_section": "chorus_1", "start_seconds": 40.0, "end_seconds": 60.0}

VALID_SHOT = {
    "id": "SHOT-deadbeef",
    "sequence_id": "SEQ-deadbeef",
    "timing": {"start_seconds": 42.0, "end_seconds": 48.5, "song_section": "chorus_1"},
    "purpose": {"semantic_event_id": "SEM-deadbeef", "narrative_function": "declaration", "editorial_function": "chorus_hero_shot"},
    "requirements": {
        "performer_id": "PERFORMER-deadbeef", "costume_id": "COSTUME-deadbeef", "world_id": "WORLD-deadbeef",
        "lip_sync_required": True, "choreography_complexity": "medium", "camera_motion": "slow_push", "character_count": 1,
    },
    "continuity": {"inherited_state": "concealed", "destination_state": "revealed"},
    "acceptance": {"identity": 95.0},
}

VALID_SHOT_2 = {
    "id": "SHOT-22222222",
    "sequence_id": "SEQ-deadbeef",
    "timing": {"start_seconds": 48.5, "end_seconds": 54.0, "song_section": "chorus_1"},
    "purpose": {"semantic_event_id": "SEM-deadbeef", "narrative_function": "declaration", "editorial_function": "chorus_hero_shot_2"},
    "requirements": {
        "performer_id": "PERFORMER-deadbeef", "costume_id": "COSTUME-deadbeef", "world_id": "WORLD-deadbeef",
        "lip_sync_required": False, "choreography_complexity": "low", "camera_motion": "static", "character_count": 1,
    },
    "continuity": {"inherited_state": "revealed", "destination_state": "declared"},
    "acceptance": {"identity": 95.0},
}

VALID_PRODUCTION_GRAPH = {
    "id": "GRAPH-deadbeef",
    "film_genome_id": "GENOME-deadbeef",
    "sequences": [VALID_SEQUENCE],
    "semantic_events": [VALID_SEMANTIC_EVENT],
    "shots": [VALID_SHOT, VALID_SHOT_2],
}


class SemanticEventSchemaTests(unittest.TestCase):
    def test_valid_semantic_event_has_no_errors(self):
        self.assertEqual(validate_semantic_event_schema(VALID_SEMANTIC_EVENT), [])

    def test_missing_meaning_is_reported(self):
        data = copy.deepcopy(VALID_SEMANTIC_EVENT)
        del data["meaning"]
        errors = validate_semantic_event_schema(data)
        self.assertTrue(any("meaning" in e for e in errors))

    def test_start_after_end_is_rejected(self):
        data = dict(VALID_SEMANTIC_EVENT, start_seconds=50.0, end_seconds=40.0)
        errors = validate_semantic_event_schema(data)
        self.assertTrue(any("start_seconds" in e for e in errors))

    def test_optional_lists_may_be_omitted(self):
        self.assertEqual(validate_semantic_event_schema(VALID_SEMANTIC_EVENT), [])


class SequenceSchemaTests(unittest.TestCase):
    def test_valid_sequence_has_no_errors(self):
        self.assertEqual(validate_sequence_schema(VALID_SEQUENCE), [])

    def test_start_after_end_is_rejected(self):
        data = dict(VALID_SEQUENCE, start_seconds=70.0, end_seconds=60.0)
        errors = validate_sequence_schema(data)
        self.assertTrue(any("start_seconds" in e for e in errors))


class ShotSchemaTests(unittest.TestCase):
    def test_valid_shot_has_no_errors(self):
        self.assertEqual(validate_shot_schema(VALID_SHOT), [])

    def test_malformed_sequence_id_is_rejected(self):
        data = dict(VALID_SHOT, sequence_id="not-a-sequence-id")
        errors = validate_shot_schema(data)
        self.assertTrue(any("sequence_id" in e for e in errors))

    def test_malformed_performer_id_is_rejected(self):
        data = copy.deepcopy(VALID_SHOT)
        data["requirements"]["performer_id"] = "not-a-performer-id"
        errors = validate_shot_schema(data)
        self.assertTrue(any("performer_id" in e for e in errors))

    def test_negative_character_count_is_rejected(self):
        data = copy.deepcopy(VALID_SHOT)
        data["requirements"]["character_count"] = 0
        errors = validate_shot_schema(data)
        self.assertTrue(any("character_count" in e for e in errors))

    def test_lip_sync_required_must_be_bool(self):
        data = copy.deepcopy(VALID_SHOT)
        data["requirements"]["lip_sync_required"] = "yes"
        errors = validate_shot_schema(data)
        self.assertTrue(any("lip_sync_required" in e for e in errors))

    def test_acceptance_score_out_of_range_is_rejected(self):
        data = dict(VALID_SHOT, acceptance={"identity": 150.0})
        errors = validate_shot_schema(data)
        self.assertTrue(any("acceptance.identity" in e for e in errors))

    def test_acceptance_score_of_zero_is_rejected(self):
        data = dict(VALID_SHOT, acceptance={"identity": 0.0})
        errors = validate_shot_schema(data)
        self.assertTrue(any("acceptance.identity" in e for e in errors))

    def test_empty_acceptance_is_rejected(self):
        data = dict(VALID_SHOT, acceptance={})
        errors = validate_shot_schema(data)
        self.assertTrue(any("acceptance" in e for e in errors))

    def test_missing_continuity_field_is_reported(self):
        data = copy.deepcopy(VALID_SHOT)
        del data["continuity"]["destination_state"]
        errors = validate_shot_schema(data)
        self.assertTrue(any("continuity.destination_state" in e for e in errors))


class ProductionGraphSchemaTests(unittest.TestCase):
    def test_valid_production_graph_has_no_errors(self):
        self.assertEqual(validate_production_graph_schema(VALID_PRODUCTION_GRAPH), [])

    def test_missing_film_genome_id_is_reported(self):
        data = copy.deepcopy(VALID_PRODUCTION_GRAPH)
        del data["film_genome_id"]
        errors = validate_production_graph_schema(data)
        self.assertTrue(any("film_genome_id" in e for e in errors))

    def test_shot_referencing_unknown_sequence_is_rejected(self):
        data = copy.deepcopy(VALID_PRODUCTION_GRAPH)
        data["shots"][0]["sequence_id"] = "SEQ-99999999"
        errors = validate_production_graph_schema(data)
        self.assertTrue(any("sequence_id" in e and "not in this graph" in e for e in errors))

    def test_shot_referencing_unknown_semantic_event_is_rejected(self):
        data = copy.deepcopy(VALID_PRODUCTION_GRAPH)
        data["shots"][0]["purpose"]["semantic_event_id"] = "SEM-99999999"
        errors = validate_production_graph_schema(data)
        self.assertTrue(any("semantic_event_id" in e and "not in this graph" in e for e in errors))

    def test_overlapping_shots_are_rejected(self):
        data = copy.deepcopy(VALID_PRODUCTION_GRAPH)
        data["shots"][1]["timing"]["start_seconds"] = 45.0  # overlaps shot 1's 42.0-48.5
        errors = validate_production_graph_schema(data)
        self.assertTrue(any("overlap" in e for e in errors))

    def test_adjacent_non_overlapping_shots_are_accepted(self):
        self.assertEqual(validate_production_graph_schema(VALID_PRODUCTION_GRAPH), [])

    def test_broken_state_inheritance_same_performer_same_sequence_is_rejected(self):
        data = copy.deepcopy(VALID_PRODUCTION_GRAPH)
        data["shots"][1]["continuity"]["inherited_state"] = "some_other_state"
        errors = validate_production_graph_schema(data)
        self.assertTrue(any("breaks state inheritance" in e for e in errors))

    def test_different_performers_do_not_require_state_chaining(self):
        data = copy.deepcopy(VALID_PRODUCTION_GRAPH)
        data["shots"][1]["requirements"]["performer_id"] = "PERFORMER-99999999"
        data["shots"][1]["continuity"]["inherited_state"] = "unrelated_state"
        errors = validate_production_graph_schema(data)
        self.assertFalse(any("breaks state inheritance" in e for e in errors))

    def test_empty_graph_is_valid(self):
        data = {"id": "GRAPH-deadbeef", "film_genome_id": "GENOME-deadbeef"}
        self.assertEqual(validate_production_graph_schema(data), [])


if __name__ == "__main__":
    unittest.main()
