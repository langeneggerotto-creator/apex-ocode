from __future__ import annotations

import unittest

from dreammusicforge.production.models import (
    ProductionGraph, SemanticEvent, Sequence, Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming,
)

SEMANTIC_EVENT_DATA = {
    "id": "SEM-deadbeef",
    "start_seconds": 42.0,
    "end_seconds": 48.5,
    "meaning": "confidence becomes declaration",
    "transformation_from": "uncertainty",
    "transformation_to": "agency",
    "intended_viewer_inference": ["she has chosen to be seen"],
    "required_visible_evidence": ["direct gaze", "forward step"],
}

SEQUENCE_DATA = {"id": "SEQ-deadbeef", "song_section": "chorus_1", "start_seconds": 40.0, "end_seconds": 60.0}

SHOT_DATA = {
    "id": "SHOT-deadbeef",
    "sequence_id": "SEQ-deadbeef",
    "timing": {"start_seconds": 42.0, "end_seconds": 48.5, "song_section": "chorus_1", "lyric_ids": ["LYRIC-018"]},
    "purpose": {"semantic_event_id": "SEM-deadbeef", "narrative_function": "declaration", "editorial_function": "chorus_hero_shot"},
    "requirements": {
        "performer_id": "PERFORMER-deadbeef", "costume_id": "COSTUME-deadbeef", "world_id": "WORLD-deadbeef",
        "lip_sync_required": True, "choreography_complexity": "medium", "camera_motion": "slow_push", "character_count": 1,
    },
    "continuity": {"inherited_state": "concealed", "permitted_mutations": ["gaze"], "destination_state": "revealed"},
    "acceptance": {"identity": 95.0, "camera_intent": 90.0},
}

PRODUCTION_GRAPH_DATA = {
    "id": "GRAPH-deadbeef",
    "film_genome_id": "GENOME-deadbeef",
    "sequences": [SEQUENCE_DATA],
    "semantic_events": [SEMANTIC_EVENT_DATA],
    "shots": [SHOT_DATA],
}


class SemanticEventRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        event = SemanticEvent.from_dict(SEMANTIC_EVENT_DATA)
        self.assertEqual(event.to_dict(), SEMANTIC_EVENT_DATA)

    def test_missing_optional_lists_default_to_empty_tuples(self):
        data = {k: v for k, v in SEMANTIC_EVENT_DATA.items() if k not in ("intended_viewer_inference", "required_visible_evidence")}
        event = SemanticEvent.from_dict(data)
        self.assertEqual(event.intended_viewer_inference, ())
        self.assertEqual(event.required_visible_evidence, ())


class SequenceRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        sequence = Sequence.from_dict(SEQUENCE_DATA)
        self.assertEqual(sequence.to_dict(), SEQUENCE_DATA)


class ShotRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        shot = Shot.from_dict(SHOT_DATA)
        self.assertEqual(shot.to_dict(), SHOT_DATA)

    def test_nested_objects_have_correct_types(self):
        shot = Shot.from_dict(SHOT_DATA)
        self.assertIsInstance(shot.timing, ShotTiming)
        self.assertIsInstance(shot.purpose, ShotPurpose)
        self.assertIsInstance(shot.requirements, ShotRequirements)
        self.assertIsInstance(shot.continuity, ShotContinuity)

    def test_shot_is_frozen(self):
        shot = Shot.from_dict(SHOT_DATA)
        with self.assertRaises(Exception):
            shot.id = "SHOT-other"  # type: ignore[misc]

    def test_requirements_character_count_is_int(self):
        shot = Shot.from_dict(SHOT_DATA)
        self.assertEqual(shot.requirements.character_count, 1)
        self.assertIsInstance(shot.requirements.character_count, int)


class ProductionGraphRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        graph = ProductionGraph.from_dict(PRODUCTION_GRAPH_DATA)
        self.assertEqual(graph.to_dict(), PRODUCTION_GRAPH_DATA)

    def test_missing_collections_default_to_empty_tuples(self):
        graph = ProductionGraph.from_dict({"id": "GRAPH-deadbeef", "film_genome_id": "GENOME-deadbeef"})
        self.assertEqual(graph.sequences, ())
        self.assertEqual(graph.semantic_events, ())
        self.assertEqual(graph.shots, ())

    def test_production_graph_is_frozen(self):
        graph = ProductionGraph.from_dict(PRODUCTION_GRAPH_DATA)
        with self.assertRaises(Exception):
            graph.id = "GRAPH-other"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
