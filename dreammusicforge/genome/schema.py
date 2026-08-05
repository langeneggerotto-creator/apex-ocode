"""Performer / Costume / World / FilmGenome JSON schema contracts.

Same dependency-free, dict-shaped, hand-walked convention as
core/schema.py and music/schema.py -- no `jsonschema` package. Each
validate_*_schema() function returns every error found, not just the
first; empty list means valid.

Referential integrity (a FilmGenome's performer_ids/costume_ids/
world_ids each actually corresponding to a Performer/Costume/World
object that exists) is deliberately NOT checked here -- these functions
only see one entity's own dict, never the full universe of entities.
genome/builder.py's assemble_film_genome() derives those id lists
directly from the Performer/Costume/World objects it's given, so a
FilmGenome built through it cannot reference a nonexistent entity by
construction -- spec Law 3.7 ("fail closed": missing references must
stop promotion) enforced structurally rather than by an after-the-fact
existence check. A FilmGenome loaded from a dict of unknown provenance
(e.g. a later release's storage layer) only gets the format check below
(does performer_ids[i] look like a well-formed PERFORMER-* id); it
cannot be checked for existence without a registry of real entities to
check against -- stated here as an honest boundary, not a silent gap.
"""
from __future__ import annotations

from .ids import is_valid_costume_id, is_valid_performer_id, is_valid_world_id

PERFORMER_SCHEMA_VERSION = "0.3.0"

PERFORMER_IMMUTABLE_FIELDS = (
    "apparent_age", "face_geometry", "body_proportions", "skin_tone", "eye_color", "identifying_features",
)
PERFORMER_MUTABLE_FIELDS = ("expression", "pose", "gaze", "costume", "hair_configuration")

WORLD_REQUIRED_STRING_FIELDS = ("type", "geometry", "palette", "lighting", "atmosphere")


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_list_of_non_empty_strs(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_non_empty_str(item) for item in value)


def _duplicates(values: list) -> list:
    seen: set = set()
    dupes: list = []
    for value in values:
        if value in seen and value not in dupes:
            dupes.append(value)
        seen.add(value)
    return dupes


def validate_performer_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["performer must be a JSON object"]

    for field_name in ("id", "display_name", "identity", "immutable", "mutable_by_contract"):
        if field_name not in data or data[field_name] in (None, "", {}):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not _is_non_empty_str(data["id"]):
        errors.append("performer id must be a non-empty string")
    if not _is_non_empty_str(data["display_name"]):
        errors.append("performer display_name must be a non-empty string")

    identity = data["identity"]
    if not isinstance(identity, dict) or not _is_list_of_non_empty_strs(identity.get("reference_assets")):
        errors.append("identity.reference_assets must be a non-empty list of non-empty strings")

    immutable = data["immutable"]
    if not isinstance(immutable, dict):
        errors.append("immutable must be an object")
    else:
        for field_name in PERFORMER_IMMUTABLE_FIELDS:
            if not _is_non_empty_str(immutable.get(field_name)):
                errors.append(f"immutable.{field_name} must be a non-empty string")

    mutable = data["mutable_by_contract"]
    if not isinstance(mutable, dict):
        errors.append("mutable_by_contract must be an object")
    else:
        for field_name in PERFORMER_MUTABLE_FIELDS:
            if not _is_non_empty_str(mutable.get(field_name)):
                errors.append(f"mutable_by_contract.{field_name} must be a non-empty string")

    return errors


def validate_costume_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["costume must be a JSON object"]

    for field_name in ("id", "topology", "material", "references"):
        if field_name not in data or data[field_name] in (None, "", {}):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not _is_non_empty_str(data["id"]):
        errors.append("costume id must be a non-empty string")
    if not isinstance(data["topology"], dict) or not data["topology"]:
        errors.append("topology must be a non-empty object")
    if not _is_non_empty_str(data["material"]):
        errors.append("material must be a non-empty string")
    if not isinstance(data["references"], dict) or not data["references"]:
        errors.append("references must be a non-empty object")

    embroidery = data.get("embroidery")
    if embroidery is not None and not _is_non_empty_str(embroidery):
        errors.append("embroidery, if present, must be a non-empty string or null")

    accessories = data.get("accessories", {})
    if not isinstance(accessories, dict):
        errors.append("accessories, if present, must be an object")

    return errors


def validate_world_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["world must be a JSON object"]

    required = ("id", "references", *WORLD_REQUIRED_STRING_FIELDS)
    for field_name in required:
        if field_name not in data or data[field_name] in (None, "", {}):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not _is_non_empty_str(data["id"]):
        errors.append("world id must be a non-empty string")
    for field_name in WORLD_REQUIRED_STRING_FIELDS:
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"{field_name} must be a non-empty string")
    if not isinstance(data["references"], dict) or not data["references"]:
        errors.append("references must be a non-empty object")

    for field_name in ("props", "allowed_transformations", "forbidden_transformations"):
        value = data.get(field_name, [])
        if not isinstance(value, list) or not all(_is_non_empty_str(item) for item in value):
            errors.append(f"{field_name}, if present, must be a list of non-empty strings")

    return errors


def validate_film_genome_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["film_genome must be a JSON object"]

    for field_name in (
        "id", "transformation", "performer_ids", "costume_ids", "world_ids",
        "camera_language", "color_language", "motifs", "invariants",
    ):
        if field_name not in data or data[field_name] in (None, "", {}, []):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not _is_non_empty_str(data["id"]):
        errors.append("film_genome id must be a non-empty string")

    transformation = data["transformation"]
    if not isinstance(transformation, dict) or not _is_non_empty_str(transformation.get("from")) or not _is_non_empty_str(transformation.get("to")):
        errors.append("transformation.from and transformation.to must both be non-empty strings")
    elif transformation["from"] == transformation["to"]:
        errors.append("transformation.from and transformation.to must differ -- a genome with no arc has no transformation")

    id_fields = (
        ("performer_ids", is_valid_performer_id, "PERFORMER-"),
        ("costume_ids", is_valid_costume_id, "COSTUME-"),
        ("world_ids", is_valid_world_id, "WORLD-"),
    )
    for field_name, is_valid, prefix in id_fields:
        values = data[field_name]
        if not isinstance(values, list) or not values:
            errors.append(f"{field_name} must be a non-empty list")
            continue
        invalid = [value for value in values if not is_valid(value)]
        if invalid:
            errors.append(f"{field_name} contains ids not matching the {prefix}* format: {invalid}")

    camera_language = data["camera_language"]
    if not isinstance(camera_language, dict):
        errors.append("camera_language must be an object")
    else:
        for field_name in ("lens_vocabulary", "movement_vocabulary"):
            if not _is_list_of_non_empty_strs(camera_language.get(field_name)):
                errors.append(f"camera_language.{field_name} must be a non-empty list of non-empty strings")

    color_language = data["color_language"]
    if not isinstance(color_language, dict):
        errors.append("color_language must be an object")
    else:
        for field_name in ("opening", "development", "climax"):
            if not _is_non_empty_str(color_language.get(field_name)):
                errors.append(f"color_language.{field_name} must be a non-empty string")

    motifs = data["motifs"]
    if not _is_list_of_non_empty_strs(motifs):
        errors.append("motifs must be a non-empty list of non-empty strings")
    else:
        duplicate_motifs = _duplicates(motifs)
        if duplicate_motifs:
            errors.append(f"motifs must be unique, duplicated: {duplicate_motifs}")

    invariants = data["invariants"]
    if not _is_list_of_non_empty_strs(invariants):
        errors.append("invariants must be a non-empty list of non-empty strings")
    else:
        duplicate_invariants = _duplicates(invariants)
        if duplicate_invariants:
            errors.append(f"invariants must be unique, duplicated: {duplicate_invariants}")

    return errors
