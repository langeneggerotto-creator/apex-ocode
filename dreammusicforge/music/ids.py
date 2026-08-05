"""Identifier generation and validation for Release 0.2's new entity
types (MasterSong, Section, LyricLine), built on the generic
generate_id()/is_valid_id() core.ids added specifically to support this
without duplicating the prefix/token logic."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

AUDIO_ID_PREFIX = "AUDIO-"
SECTION_ID_PREFIX = "SECTION-"
LYRIC_ID_PREFIX = "LYRIC-"


def generate_audio_id() -> str:
    return generate_id(AUDIO_ID_PREFIX)


def is_valid_audio_id(value: object) -> bool:
    return is_valid_id(value, AUDIO_ID_PREFIX)


def generate_section_id() -> str:
    return generate_id(SECTION_ID_PREFIX)


def is_valid_section_id(value: object) -> bool:
    return is_valid_id(value, SECTION_ID_PREFIX)


def generate_lyric_id() -> str:
    return generate_id(LYRIC_ID_PREFIX)


def is_valid_lyric_id(value: object) -> bool:
    return is_valid_id(value, LYRIC_ID_PREFIX)
