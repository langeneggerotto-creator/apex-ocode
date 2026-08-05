from __future__ import annotations

import copy
import unittest

from dreammusicforge.genome.schema import (
    validate_costume_schema, validate_film_genome_schema, validate_performer_schema, validate_world_schema,
)

VALID_PERFORMER = {
    "id": "PERFORMER-deadbeef",
    "display_name": "Nola",
    "identity": {"reference_assets": ["face_front.png"]},
    "immutable": {
        "apparent_age": "late 20s",
        "face_geometry": "oval",
        "body_proportions": "average",
        "skin_tone": "warm olive",
        "eye_color": "dark brown",
        "identifying_features": "small mole above lip",
    },
    "mutable_by_contract": {
        "expression": "varies", "pose": "varies", "gaze": "varies", "costume": "varies", "hair_configuration": "varies",
    },
}

VALID_COSTUME = {
    "id": "COSTUME-deadbeef",
    "topology": {"neckline": "symmetrical_square"},
    "material": "satin",
    "references": {"front": "costume_front.png"},
}

VALID_WORLD = {
    "id": "WORLD-deadbeef",
    "type": "physical_theatrical_stage",
    "references": {"wide": "stage_wide.png"},
    "geometry": "proscenium stage",
    "palette": "deep blue",
    "lighting": "cool wash",
    "atmosphere": "light haze",
}

VALID_FILM_GENOME = {
    "id": "GENOME-deadbeef",
    "transformation": {"from": "concealment", "to": "self-expression"},
    "performer_ids": ["PERFORMER-deadbeef"],
    "costume_ids": ["COSTUME-deadbeef"],
    "world_ids": ["WORLD-deadbeef"],
    "camera_language": {"lens_vocabulary": ["35mm"], "movement_vocabulary": ["slow_push"]},
    "color_language": {"opening": "amber_crimson", "development": "blue_pearl", "climax": "red_gold"},
    "motifs": ["threshold", "circular_opening"],
    "invariants": ["lead_performer_identity", "master_song"],
}


class PerformerSchemaTests(unittest.TestCase):
    def test_valid_performer_has_no_errors(self):
        self.assertEqual(validate_performer_schema(VALID_PERFORMER), [])

    def test_non_dict_is_rejected(self):
        self.assertTrue(validate_performer_schema(["not", "a", "dict"]))

    def test_missing_required_field_is_reported(self):
        data = copy.deepcopy(VALID_PERFORMER)
        del data["display_name"]
        errors = validate_performer_schema(data)
        self.assertTrue(any("display_name" in e for e in errors))

    def test_empty_reference_assets_is_rejected(self):
        data = copy.deepcopy(VALID_PERFORMER)
        data["identity"] = {"reference_assets": []}
        errors = validate_performer_schema(data)
        self.assertTrue(any("reference_assets" in e for e in errors))

    def test_missing_immutable_field_is_reported(self):
        data = copy.deepcopy(VALID_PERFORMER)
        del data["immutable"]["eye_color"]
        errors = validate_performer_schema(data)
        self.assertTrue(any("immutable.eye_color" in e for e in errors))

    def test_empty_immutable_field_is_rejected(self):
        data = copy.deepcopy(VALID_PERFORMER)
        data["immutable"]["eye_color"] = ""
        errors = validate_performer_schema(data)
        self.assertTrue(any("immutable.eye_color" in e for e in errors))

    def test_missing_mutable_field_is_reported(self):
        data = copy.deepcopy(VALID_PERFORMER)
        del data["mutable_by_contract"]["gaze"]
        errors = validate_performer_schema(data)
        self.assertTrue(any("mutable_by_contract.gaze" in e for e in errors))


class CostumeSchemaTests(unittest.TestCase):
    def test_valid_costume_has_no_errors(self):
        self.assertEqual(validate_costume_schema(VALID_COSTUME), [])

    def test_empty_topology_is_rejected(self):
        data = dict(VALID_COSTUME, topology={})
        errors = validate_costume_schema(data)
        self.assertTrue(any("topology" in e for e in errors))

    def test_missing_material_is_reported(self):
        data = copy.deepcopy(VALID_COSTUME)
        del data["material"]
        errors = validate_costume_schema(data)
        self.assertTrue(any("material" in e for e in errors))

    def test_embroidery_may_be_omitted(self):
        self.assertEqual(validate_costume_schema(VALID_COSTUME), [])

    def test_empty_string_embroidery_is_rejected(self):
        data = dict(VALID_COSTUME, embroidery="")
        errors = validate_costume_schema(data)
        self.assertTrue(any("embroidery" in e for e in errors))

    def test_null_embroidery_is_accepted(self):
        data = dict(VALID_COSTUME, embroidery=None)
        self.assertEqual(validate_costume_schema(data), [])

    def test_empty_references_is_rejected(self):
        data = dict(VALID_COSTUME, references={})
        errors = validate_costume_schema(data)
        self.assertTrue(any("references" in e for e in errors))


class WorldSchemaTests(unittest.TestCase):
    def test_valid_world_has_no_errors(self):
        self.assertEqual(validate_world_schema(VALID_WORLD), [])

    def test_missing_geometry_is_reported(self):
        data = copy.deepcopy(VALID_WORLD)
        del data["geometry"]
        errors = validate_world_schema(data)
        self.assertTrue(any("geometry" in e for e in errors))

    def test_empty_lighting_is_rejected(self):
        data = dict(VALID_WORLD, lighting="")
        errors = validate_world_schema(data)
        self.assertTrue(any("lighting" in e for e in errors))

    def test_optional_lists_may_be_omitted(self):
        self.assertEqual(validate_world_schema(VALID_WORLD), [])

    def test_props_must_be_list_of_non_empty_strings(self):
        data = dict(VALID_WORLD, props=["mic", ""])
        errors = validate_world_schema(data)
        self.assertTrue(any("props" in e for e in errors))


class FilmGenomeSchemaTests(unittest.TestCase):
    def test_valid_film_genome_has_no_errors(self):
        self.assertEqual(validate_film_genome_schema(VALID_FILM_GENOME), [])

    def test_missing_transformation_is_reported(self):
        data = copy.deepcopy(VALID_FILM_GENOME)
        del data["transformation"]
        errors = validate_film_genome_schema(data)
        self.assertTrue(any("transformation" in e for e in errors))

    def test_transformation_from_equal_to_is_rejected(self):
        data = dict(VALID_FILM_GENOME, transformation={"from": "concealment", "to": "concealment"})
        errors = validate_film_genome_schema(data)
        self.assertTrue(any("differ" in e for e in errors))

    def test_empty_performer_ids_is_rejected(self):
        data = dict(VALID_FILM_GENOME, performer_ids=[])
        errors = validate_film_genome_schema(data)
        self.assertTrue(any("performer_ids" in e for e in errors))

    def test_malformed_performer_id_is_rejected(self):
        data = dict(VALID_FILM_GENOME, performer_ids=["not-a-performer-id"])
        errors = validate_film_genome_schema(data)
        self.assertTrue(any("performer_ids" in e for e in errors))

    def test_wrong_prefix_costume_id_is_rejected(self):
        data = dict(VALID_FILM_GENOME, costume_ids=["PERFORMER-deadbeef"])
        errors = validate_film_genome_schema(data)
        self.assertTrue(any("costume_ids" in e for e in errors))

    def test_missing_camera_language_field_is_reported(self):
        data = copy.deepcopy(VALID_FILM_GENOME)
        del data["camera_language"]["movement_vocabulary"]
        errors = validate_film_genome_schema(data)
        self.assertTrue(any("movement_vocabulary" in e for e in errors))

    def test_missing_color_language_field_is_reported(self):
        data = copy.deepcopy(VALID_FILM_GENOME)
        del data["color_language"]["climax"]
        errors = validate_film_genome_schema(data)
        self.assertTrue(any("color_language.climax" in e for e in errors))

    def test_duplicate_motifs_are_rejected(self):
        data = dict(VALID_FILM_GENOME, motifs=["threshold", "threshold"])
        errors = validate_film_genome_schema(data)
        self.assertTrue(any("motifs" in e and "duplicated" in e for e in errors))

    def test_duplicate_invariants_are_rejected(self):
        data = dict(VALID_FILM_GENOME, invariants=["master_song", "master_song"])
        errors = validate_film_genome_schema(data)
        self.assertTrue(any("invariants" in e and "duplicated" in e for e in errors))

    def test_empty_motifs_is_rejected(self):
        data = dict(VALID_FILM_GENOME, motifs=[])
        errors = validate_film_genome_schema(data)
        self.assertTrue(any("motifs" in e for e in errors))

    def test_multiple_performer_costume_world_ids_are_accepted(self):
        data = dict(
            VALID_FILM_GENOME,
            performer_ids=["PERFORMER-deadbeef", "PERFORMER-11111111"],
            costume_ids=["COSTUME-deadbeef", "COSTUME-22222222"],
            world_ids=["WORLD-deadbeef", "WORLD-33333333"],
        )
        self.assertEqual(validate_film_genome_schema(data), [])


if __name__ == "__main__":
    unittest.main()
