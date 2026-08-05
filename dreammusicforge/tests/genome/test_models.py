from __future__ import annotations

import unittest

from dreammusicforge.genome.models import (
    CameraLanguage, ColorLanguage, Costume, FilmGenome, Performer, World,
)

PERFORMER_DATA = {
    "id": "PERFORMER-deadbeef",
    "display_name": "Nola",
    "identity": {"reference_assets": ["face_front.png", "full_body_front.png"]},
    "immutable": {
        "apparent_age": "late 20s",
        "face_geometry": "oval, high cheekbones",
        "body_proportions": "average, athletic",
        "skin_tone": "warm olive",
        "eye_color": "dark brown",
        "identifying_features": "small mole above lip",
    },
    "mutable_by_contract": {
        "expression": "varies by shot",
        "pose": "varies by shot",
        "gaze": "varies by shot",
        "costume": "varies by shot",
        "hair_configuration": "varies by shot",
    },
}

COSTUME_DATA = {
    "id": "COSTUME-deadbeef",
    "topology": {"neckline": "symmetrical_square", "straps": "2", "sleeves": "none"},
    "material": "satin",
    "embroidery": "geometric_gold",
    "accessories": {"earrings": "small_gold_studs"},
    "references": {"front": "costume_front.png", "back": "costume_back.png"},
}

WORLD_DATA = {
    "id": "WORLD-deadbeef",
    "type": "physical_theatrical_stage",
    "references": {"wide": "stage_wide.png", "medium": "stage_medium.png"},
    "geometry": "proscenium stage, 12m wide",
    "palette": "deep blue with amber accents",
    "lighting": "single key light, cool wash",
    "atmosphere": "light haze",
    "props": ["standing_mic"],
    "allowed_transformations": ["lighting_shift"],
    "forbidden_transformations": ["geometry_change"],
}

FILM_GENOME_DATA = {
    "id": "GENOME-deadbeef",
    "transformation": {"from": "concealment", "to": "self-expression"},
    "performer_ids": ["PERFORMER-deadbeef"],
    "costume_ids": ["COSTUME-deadbeef"],
    "world_ids": ["WORLD-deadbeef"],
    "camera_language": {"lens_vocabulary": ["35mm", "50mm"], "movement_vocabulary": ["slow_push"]},
    "color_language": {"opening": "amber_crimson", "development": "blue_pearl", "climax": "red_gold"},
    "motifs": ["threshold", "circular_opening"],
    "invariants": ["lead_performer_identity", "master_song"],
}


class PerformerRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        performer = Performer.from_dict(PERFORMER_DATA)
        self.assertEqual(performer.to_dict(), PERFORMER_DATA)

    def test_performer_is_frozen(self):
        performer = Performer.from_dict(PERFORMER_DATA)
        with self.assertRaises(Exception):
            performer.display_name = "Changed"  # type: ignore[misc]


class CostumeRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        costume = Costume.from_dict(COSTUME_DATA)
        self.assertEqual(costume.to_dict(), COSTUME_DATA)

    def test_missing_embroidery_defaults_to_none(self):
        data = {k: v for k, v in COSTUME_DATA.items() if k != "embroidery"}
        costume = Costume.from_dict(data)
        self.assertIsNone(costume.embroidery)

    def test_missing_accessories_defaults_to_empty_dict(self):
        data = {k: v for k, v in COSTUME_DATA.items() if k != "accessories"}
        costume = Costume.from_dict(data)
        self.assertEqual(costume.accessories, {})


class WorldRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        world = World.from_dict(WORLD_DATA)
        self.assertEqual(world.to_dict(), WORLD_DATA)

    def test_missing_optional_lists_default_to_empty_tuples(self):
        data = {k: v for k, v in WORLD_DATA.items() if k not in ("props", "allowed_transformations", "forbidden_transformations")}
        world = World.from_dict(data)
        self.assertEqual(world.props, ())
        self.assertEqual(world.allowed_transformations, ())
        self.assertEqual(world.forbidden_transformations, ())


class CameraLanguageRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        data = {"lens_vocabulary": ["35mm"], "movement_vocabulary": ["slow_push"]}
        camera_language = CameraLanguage.from_dict(data)
        self.assertEqual(camera_language.to_dict(), data)


class ColorLanguageRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        data = {"opening": "amber_crimson", "development": "blue_pearl", "climax": "red_gold"}
        color_language = ColorLanguage.from_dict(data)
        self.assertEqual(color_language.to_dict(), data)


class FilmGenomeRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        genome = FilmGenome.from_dict(FILM_GENOME_DATA)
        self.assertEqual(genome.to_dict(), FILM_GENOME_DATA)

    def test_transformation_from_and_to_are_separate_fields(self):
        genome = FilmGenome.from_dict(FILM_GENOME_DATA)
        self.assertEqual(genome.transformation_from, "concealment")
        self.assertEqual(genome.transformation_to, "self-expression")

    def test_film_genome_is_frozen(self):
        genome = FilmGenome.from_dict(FILM_GENOME_DATA)
        with self.assertRaises(Exception):
            genome.id = "GENOME-other"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
