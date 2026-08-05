from __future__ import annotations

import unittest

from dreammusicforge.genome.builder import assemble_film_genome, build_costume, build_performer, build_world
from dreammusicforge.genome.errors import GenomeValidationError
from dreammusicforge.genome.ids import generate_performer_id
from dreammusicforge.genome.models import CameraLanguage, ColorLanguage

IMMUTABLE = {
    "apparent_age": "late 20s",
    "face_geometry": "oval, high cheekbones",
    "body_proportions": "average, athletic",
    "skin_tone": "warm olive",
    "eye_color": "dark brown",
    "identifying_features": "small mole above lip",
}
MUTABLE = {
    "expression": "varies by shot", "pose": "varies by shot", "gaze": "varies by shot",
    "costume": "varies by shot", "hair_configuration": "varies by shot",
}


def _build_performer():
    return build_performer(
        display_name="Nola",
        reference_assets=("face_front.png", "full_body_front.png"),
        immutable=IMMUTABLE,
        mutable_by_contract=MUTABLE,
    )


def _build_costume():
    return build_costume(
        topology={"neckline": "symmetrical_square", "sleeves": "none"},
        material="satin",
        references={"front": "costume_front.png", "back": "costume_back.png"},
        embroidery="geometric_gold",
    )


def _build_world():
    return build_world(
        type="physical_theatrical_stage",
        references={"wide": "stage_wide.png", "medium": "stage_medium.png"},
        geometry="proscenium stage, 12m wide",
        palette="deep blue with amber accents",
        lighting="single key light, cool wash",
        atmosphere="light haze",
    )


class BuildPerformerTests(unittest.TestCase):
    def test_builds_a_valid_performer(self):
        performer = _build_performer()
        self.assertTrue(performer.id.startswith("PERFORMER-"))
        self.assertEqual(performer.display_name, "Nola")
        self.assertEqual(performer.immutable, IMMUTABLE)

    def test_explicit_performer_id_is_used(self):
        chosen_id = generate_performer_id()
        performer = build_performer(
            display_name="Nola", reference_assets=("a.png",), immutable=IMMUTABLE,
            mutable_by_contract=MUTABLE, performer_id=chosen_id,
        )
        self.assertEqual(performer.id, chosen_id)

    def test_missing_immutable_field_raises(self):
        bad_immutable = dict(IMMUTABLE)
        del bad_immutable["eye_color"]
        with self.assertRaises(GenomeValidationError):
            build_performer(display_name="Nola", reference_assets=("a.png",), immutable=bad_immutable, mutable_by_contract=MUTABLE)

    def test_empty_reference_assets_raises(self):
        with self.assertRaises(GenomeValidationError):
            build_performer(display_name="Nola", reference_assets=(), immutable=IMMUTABLE, mutable_by_contract=MUTABLE)


class BuildCostumeTests(unittest.TestCase):
    def test_builds_a_valid_costume(self):
        costume = _build_costume()
        self.assertTrue(costume.id.startswith("COSTUME-"))
        self.assertEqual(costume.material, "satin")

    def test_empty_topology_raises(self):
        with self.assertRaises(GenomeValidationError):
            build_costume(topology={}, material="satin", references={"front": "a.png"})


class BuildWorldTests(unittest.TestCase):
    def test_builds_a_valid_world(self):
        world = _build_world()
        self.assertTrue(world.id.startswith("WORLD-"))
        self.assertEqual(world.type, "physical_theatrical_stage")

    def test_missing_geometry_raises(self):
        with self.assertRaises(GenomeValidationError):
            build_world(type="stage", references={"wide": "a.png"}, geometry="", palette="blue", lighting="cool", atmosphere="haze")


class AssembleFilmGenomeTests(unittest.TestCase):
    def setUp(self):
        self.performer = _build_performer()
        self.costume = _build_costume()
        self.world = _build_world()

    def test_a_complete_film_genome_can_be_created_and_validated(self):
        """Release 0.3's stated acceptance test (spec section 19): a
        complete Film Genome can be created and validated."""
        genome = assemble_film_genome(
            transformation_from="concealment",
            transformation_to="self-expression",
            performers=(self.performer,),
            costumes=(self.costume,),
            worlds=(self.world,),
            camera_language=CameraLanguage(lens_vocabulary=("35mm", "50mm"), movement_vocabulary=("slow_push", "controlled_orbit")),
            color_language=ColorLanguage(opening="amber_crimson", development="blue_pearl", climax="red_gold"),
            motifs=("threshold", "circular_opening", "hand_to_heart"),
            invariants=("lead_performer_identity", "master_song", "narrative_transformation"),
        )

        self.assertTrue(genome.id.startswith("GENOME-"))
        self.assertEqual(genome.performer_ids, (self.performer.id,))
        self.assertEqual(genome.costume_ids, (self.costume.id,))
        self.assertEqual(genome.world_ids, (self.world.id,))

    def test_genome_cannot_reference_a_nonexistent_entity_by_construction(self):
        """assemble_film_genome() derives its id lists from the objects
        given to it -- there is no parameter through which a caller could
        supply a dangling performer/costume/world id."""
        genome = assemble_film_genome(
            transformation_from="concealment", transformation_to="self-expression",
            performers=(self.performer,), costumes=(self.costume,), worlds=(self.world,),
            camera_language=CameraLanguage(lens_vocabulary=("35mm",), movement_vocabulary=("slow_push",)),
            color_language=ColorLanguage(opening="a", development="b", climax="c"),
            motifs=("threshold",), invariants=("master_song",),
        )
        self.assertEqual(set(genome.performer_ids), {self.performer.id})

    def test_same_transformation_from_and_to_raises(self):
        with self.assertRaises(GenomeValidationError):
            assemble_film_genome(
                transformation_from="concealment", transformation_to="concealment",
                performers=(self.performer,), costumes=(self.costume,), worlds=(self.world,),
                camera_language=CameraLanguage(lens_vocabulary=("35mm",), movement_vocabulary=("slow_push",)),
                color_language=ColorLanguage(opening="a", development="b", climax="c"),
                motifs=("threshold",), invariants=("master_song",),
            )

    def test_no_performers_raises(self):
        with self.assertRaises(GenomeValidationError):
            assemble_film_genome(
                transformation_from="concealment", transformation_to="self-expression",
                performers=(), costumes=(self.costume,), worlds=(self.world,),
                camera_language=CameraLanguage(lens_vocabulary=("35mm",), movement_vocabulary=("slow_push",)),
                color_language=ColorLanguage(opening="a", development="b", climax="c"),
                motifs=("threshold",), invariants=("master_song",),
            )

    def test_duplicate_motifs_raise_with_every_problem_carried(self):
        try:
            assemble_film_genome(
                transformation_from="concealment", transformation_to="self-expression",
                performers=(), costumes=(), worlds=(),
                camera_language=CameraLanguage(lens_vocabulary=(), movement_vocabulary=()),
                color_language=ColorLanguage(opening="", development="", climax=""),
                motifs=("threshold", "threshold"), invariants=(),
            )
            self.fail("expected GenomeValidationError")
        except GenomeValidationError as exc:
            self.assertGreaterEqual(len(exc.errors), 2)


if __name__ == "__main__":
    unittest.main()
