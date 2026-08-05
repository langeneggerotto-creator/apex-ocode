from __future__ import annotations

import unittest

from dreammusicforge.genome.builder import assemble_film_genome, build_costume, build_performer, build_world
from dreammusicforge.genome.models import CameraLanguage, ColorLanguage
from dreammusicforge.production.builder import (
    assemble_production_graph, build_semantic_event, build_sequence, build_shot,
)
from dreammusicforge.production.errors import ProductionGraphValidationError
from dreammusicforge.production.models import ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming

IMMUTABLE = {
    "apparent_age": "late 20s", "face_geometry": "oval", "body_proportions": "average",
    "skin_tone": "warm olive", "eye_color": "dark brown", "identifying_features": "small mole above lip",
}
MUTABLE = {"expression": "v", "pose": "v", "gaze": "v", "costume": "v", "hair_configuration": "v"}


def _build_genome():
    performer = build_performer(display_name="Nola", reference_assets=("a.png",), immutable=IMMUTABLE, mutable_by_contract=MUTABLE)
    costume = build_costume(topology={"neckline": "square"}, material="satin", references={"front": "a.png"})
    world = build_world(type="stage", references={"wide": "a.png"}, geometry="g", palette="p", lighting="l", atmosphere="a")
    genome = assemble_film_genome(
        transformation_from="concealment", transformation_to="self-expression",
        performers=(performer,), costumes=(costume,), worlds=(world,),
        camera_language=CameraLanguage(lens_vocabulary=("35mm",), movement_vocabulary=("slow_push",)),
        color_language=ColorLanguage(opening="a", development="b", climax="c"),
        motifs=("threshold",), invariants=("master_song",),
    )
    return genome, performer, costume, world


class BuildSemanticEventTests(unittest.TestCase):
    def test_builds_a_valid_semantic_event(self):
        event = build_semantic_event(
            start_seconds=42.0, end_seconds=48.5, meaning="confidence becomes declaration",
            transformation_from="uncertainty", transformation_to="agency",
        )
        self.assertTrue(event.id.startswith("SEM-"))
        self.assertEqual(event.meaning, "confidence becomes declaration")

    def test_end_before_start_raises(self):
        with self.assertRaises(ProductionGraphValidationError):
            build_semantic_event(start_seconds=50.0, end_seconds=40.0, meaning="m", transformation_from="a", transformation_to="b")


class BuildSequenceTests(unittest.TestCase):
    def test_builds_a_valid_sequence(self):
        sequence = build_sequence(song_section="chorus_1", start_seconds=40.0, end_seconds=60.0)
        self.assertTrue(sequence.id.startswith("SEQ-"))

    def test_end_before_start_raises(self):
        with self.assertRaises(ProductionGraphValidationError):
            build_sequence(song_section="chorus_1", start_seconds=60.0, end_seconds=40.0)


class BuildShotTests(unittest.TestCase):
    def setUp(self):
        self.genome, self.performer, self.costume, self.world = _build_genome()
        self.sequence = build_sequence(song_section="chorus_1", start_seconds=40.0, end_seconds=60.0)
        self.event = build_semantic_event(start_seconds=42.0, end_seconds=48.5, meaning="m", transformation_from="a", transformation_to="b")

    def test_builds_a_valid_shot(self):
        shot = build_shot(
            sequence_id=self.sequence.id,
            timing=ShotTiming(start_seconds=42.0, end_seconds=48.5, song_section="chorus_1"),
            purpose=ShotPurpose(semantic_event_id=self.event.id, narrative_function="declaration", editorial_function="chorus_hero_shot"),
            requirements=ShotRequirements(
                performer_id=self.performer.id, costume_id=self.costume.id, world_id=self.world.id,
                lip_sync_required=True, choreography_complexity="medium", camera_motion="slow_push", character_count=1,
            ),
            continuity=ShotContinuity(inherited_state="concealed", permitted_mutations=("gaze",), destination_state="revealed"),
            acceptance={"identity": 95.0},
        )
        self.assertTrue(shot.id.startswith("SHOT-"))

    def test_invalid_acceptance_score_raises(self):
        with self.assertRaises(ProductionGraphValidationError):
            build_shot(
                sequence_id=self.sequence.id,
                timing=ShotTiming(start_seconds=42.0, end_seconds=48.5, song_section="chorus_1"),
                purpose=ShotPurpose(semantic_event_id=self.event.id, narrative_function="declaration", editorial_function="hero"),
                requirements=ShotRequirements(
                    performer_id=self.performer.id, costume_id=self.costume.id, world_id=self.world.id,
                    lip_sync_required=True, choreography_complexity="medium", camera_motion="slow_push", character_count=1,
                ),
                continuity=ShotContinuity(inherited_state="concealed", permitted_mutations=(), destination_state="revealed"),
                acceptance={"identity": 200.0},
            )


class AssembleProductionGraphTests(unittest.TestCase):
    def setUp(self):
        self.genome, self.performer, self.costume, self.world = _build_genome()
        self.sequence = build_sequence(song_section="chorus_1", start_seconds=40.0, end_seconds=60.0)
        self.event = build_semantic_event(start_seconds=42.0, end_seconds=54.0, meaning="m", transformation_from="a", transformation_to="b")

    def _shot(self, start, end, inherited_state, destination_state, shot_id=None):
        return build_shot(
            sequence_id=self.sequence.id,
            timing=ShotTiming(start_seconds=start, end_seconds=end, song_section="chorus_1"),
            purpose=ShotPurpose(semantic_event_id=self.event.id, narrative_function="declaration", editorial_function="hero"),
            requirements=ShotRequirements(
                performer_id=self.performer.id, costume_id=self.costume.id, world_id=self.world.id,
                lip_sync_required=False, choreography_complexity="medium", camera_motion="slow_push", character_count=1,
            ),
            continuity=ShotContinuity(inherited_state=inherited_state, permitted_mutations=(), destination_state=destination_state),
            acceptance={"identity": 95.0},
            shot_id=shot_id,
        )

    def test_project_compiles_into_an_ordered_production_graph(self):
        """Release 0.4's stated acceptance test (spec section 19):
        project compiles into an ordered production graph."""
        shot_a = self._shot(42.0, 48.0, "concealed", "revealed")
        shot_b = self._shot(48.0, 54.0, "revealed", "declared")

        graph = assemble_production_graph(
            film_genome=self.genome, sequences=(self.sequence,), semantic_events=(self.event,),
            shots=(shot_b, shot_a),  # deliberately out of order
        )

        self.assertTrue(graph.id.startswith("GRAPH-"))
        self.assertEqual(graph.film_genome_id, self.genome.id)
        self.assertEqual([shot.id for shot in graph.shots], [shot_a.id, shot_b.id])

    def test_shot_referencing_unknown_performer_raises(self):
        shot = self._shot(42.0, 48.0, "concealed", "revealed")
        bad_requirements = ShotRequirements(
            performer_id="PERFORMER-99999999", costume_id=self.costume.id, world_id=self.world.id,
            lip_sync_required=False, choreography_complexity="medium", camera_motion="slow_push", character_count=1,
        )
        from dreammusicforge.production.models import Shot
        bad_shot = Shot(id=shot.id, sequence_id=shot.sequence_id, timing=shot.timing, purpose=shot.purpose,
                         requirements=bad_requirements, continuity=shot.continuity, acceptance=shot.acceptance)
        with self.assertRaises(ProductionGraphValidationError):
            assemble_production_graph(film_genome=self.genome, sequences=(self.sequence,), semantic_events=(self.event,), shots=(bad_shot,))

    def test_overlapping_shots_raise(self):
        shot_a = self._shot(42.0, 50.0, "concealed", "revealed")
        shot_b = self._shot(48.0, 54.0, "revealed", "declared")
        with self.assertRaises(ProductionGraphValidationError):
            assemble_production_graph(film_genome=self.genome, sequences=(self.sequence,), semantic_events=(self.event,), shots=(shot_a, shot_b))

    def test_broken_state_inheritance_raises(self):
        shot_a = self._shot(42.0, 48.0, "concealed", "revealed")
        shot_b = self._shot(48.0, 54.0, "some_unrelated_state", "declared")
        with self.assertRaises(ProductionGraphValidationError):
            assemble_production_graph(film_genome=self.genome, sequences=(self.sequence,), semantic_events=(self.event,), shots=(shot_a, shot_b))

    def test_error_carries_every_problem_found(self):
        shot_a = self._shot(42.0, 50.0, "concealed", "revealed")
        shot_b = self._shot(48.0, 54.0, "some_unrelated_state", "declared")
        try:
            assemble_production_graph(film_genome=self.genome, sequences=(self.sequence,), semantic_events=(self.event,), shots=(shot_a, shot_b))
            self.fail("expected ProductionGraphValidationError")
        except ProductionGraphValidationError as exc:
            self.assertGreaterEqual(len(exc.errors), 2)


if __name__ == "__main__":
    unittest.main()
