"""Identifier generation and validation for Release 0.3's new entity
types (Performer, Costume, World, FilmGenome), built on the generic
generate_id()/is_valid_id() core.ids added in Release 0.2 for exactly
this purpose -- same pattern as music/ids.py."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

PERFORMER_ID_PREFIX = "PERFORMER-"
COSTUME_ID_PREFIX = "COSTUME-"
WORLD_ID_PREFIX = "WORLD-"
GENOME_ID_PREFIX = "GENOME-"


def generate_performer_id() -> str:
    return generate_id(PERFORMER_ID_PREFIX)


def is_valid_performer_id(value: object) -> bool:
    return is_valid_id(value, PERFORMER_ID_PREFIX)


def generate_costume_id() -> str:
    return generate_id(COSTUME_ID_PREFIX)


def is_valid_costume_id(value: object) -> bool:
    return is_valid_id(value, COSTUME_ID_PREFIX)


def generate_world_id() -> str:
    return generate_id(WORLD_ID_PREFIX)


def is_valid_world_id(value: object) -> bool:
    return is_valid_id(value, WORLD_ID_PREFIX)


def generate_genome_id() -> str:
    return generate_id(GENOME_ID_PREFIX)


def is_valid_genome_id(value: object) -> bool:
    return is_valid_id(value, GENOME_ID_PREFIX)
