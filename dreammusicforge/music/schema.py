"""MasterSong / Timeline JSON schema contracts.

Same dependency-free, dict-shaped, hand-walked convention as
core/schema.py -- no `jsonschema` package, contract stays inspectable as
plain data. Each validate_*_schema() function returns every error found,
not just the first; empty list means valid.
"""
from __future__ import annotations

from .models import SECTION_TYPES

MASTER_SONG_SCHEMA_VERSION = "0.2.0"

MASTER_SONG_SCHEMA: dict = {
    "$id": "dreammusicforge/music/schema.py:MASTER_SONG_SCHEMA",
    "schema_version": MASTER_SONG_SCHEMA_VERSION,
    "type": "object",
    "required": [
        "id", "source_file", "duration_seconds", "sample_rate", "channels",
        "bpm", "time_signature", "hash",
    ],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "source_file": {"type": "string", "minLength": 1},
        "duration_seconds": {"type": "number", "exclusiveMinimum": 0},
        "sample_rate": {"type": "number", "exclusiveMinimum": 0},
        "channels": {"type": "number", "exclusiveMinimum": 0},
        "bpm": {"type": "number", "exclusiveMinimum": 0},
        "time_signature": {"type": "string", "minLength": 1},
        "hash": {"type": "string", "minLength": 1},
        "stems": {"type": "object", "optional": True},
    },
}

SECTION_SCHEMA: dict = {
    "$id": "dreammusicforge/music/schema.py:SECTION_SCHEMA",
    "type": "object",
    "required": ["id", "type", "start_seconds", "end_seconds"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "type": {"enum": sorted(SECTION_TYPES)},
        "start_seconds": {"type": "number", "minimum": 0},
        "end_seconds": {"type": "number", "exclusiveMinimum": 0},
        "label": {"type": ["string", "null"], "optional": True},
    },
}

BEAT_SCHEMA: dict = {
    "$id": "dreammusicforge/music/schema.py:BEAT_SCHEMA",
    "type": "object",
    "required": ["index", "time", "bar", "beat_in_bar"],
    "properties": {
        "index": {"type": "number", "minimum": 0},
        "time": {"type": "number", "minimum": 0},
        "bar": {"type": "number", "exclusiveMinimum": 0},
        "beat_in_bar": {"type": "number", "exclusiveMinimum": 0},
    },
}

LYRIC_LINE_SCHEMA: dict = {
    "$id": "dreammusicforge/music/schema.py:LYRIC_LINE_SCHEMA",
    "type": "object",
    "required": ["id", "start_seconds", "end_seconds", "text"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "start_seconds": {"type": "number", "minimum": 0},
        "end_seconds": {"type": "number", "exclusiveMinimum": 0},
        "text": {"type": "string", "minLength": 1},
    },
}

TIMELINE_SCHEMA_VERSION = "0.2.0"


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_master_song_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["master_song must be a JSON object"]

    for field_name in MASTER_SONG_SCHEMA["required"]:
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    for field_name in ("id", "source_file", "time_signature", "hash"):
        if not isinstance(data[field_name], str) or not data[field_name]:
            errors.append(f"{field_name} must be a non-empty string")

    for field_name in ("duration_seconds", "bpm"):
        value = data[field_name]
        if not _is_number(value) or value <= 0:
            errors.append(f"{field_name} must be a positive number")

    for field_name in ("sample_rate", "channels"):
        value = data[field_name]
        if not _is_number(value) or value <= 0:
            errors.append(f"{field_name} must be a positive number")

    stems = data.get("stems", {})
    if not isinstance(stems, dict):
        errors.append("stems, if present, must be an object")
    elif not all(isinstance(k, str) and isinstance(v, str) for k, v in stems.items()):
        errors.append("stems must map string keys to string values")

    return errors


def validate_section_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["section must be a JSON object"]

    for field_name in SECTION_SCHEMA["required"]:
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not isinstance(data["id"], str) or not data["id"]:
        errors.append("section id must be a non-empty string")
    if data["type"] not in SECTION_TYPES:
        errors.append(f"section type must be one of {sorted(SECTION_TYPES)}, got {data['type']!r}")

    start = data["start_seconds"]
    end = data["end_seconds"]
    if not _is_number(start) or start < 0:
        errors.append("section start_seconds must be a non-negative number")
    if not _is_number(end) or end <= 0:
        errors.append("section end_seconds must be a positive number")
    if _is_number(start) and _is_number(end) and start >= end:
        errors.append(f"section start_seconds ({start}) must be before end_seconds ({end})")

    label = data.get("label")
    if label is not None and (not isinstance(label, str) or not label):
        errors.append("section label, if present, must be a non-empty string or null")

    return errors


def validate_beat_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["beat must be a JSON object"]

    for field_name in BEAT_SCHEMA["required"]:
        if field_name not in data:
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    index = data["index"]
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        errors.append("beat index must be a non-negative integer")

    time = data["time"]
    if not _is_number(time) or time < 0:
        errors.append("beat time must be a non-negative number")

    for field_name in ("bar", "beat_in_bar"):
        value = data[field_name]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"beat {field_name} must be a positive integer")

    return errors


def validate_lyric_line_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["lyric line must be a JSON object"]

    for field_name in LYRIC_LINE_SCHEMA["required"]:
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not isinstance(data["id"], str) or not data["id"]:
        errors.append("lyric line id must be a non-empty string")
    if not isinstance(data["text"], str) or not data["text"]:
        errors.append("lyric line text must be a non-empty string")

    start = data["start_seconds"]
    end = data["end_seconds"]
    if not _is_number(start) or start < 0:
        errors.append("lyric line start_seconds must be a non-negative number")
    if not _is_number(end) or end <= 0:
        errors.append("lyric line end_seconds must be a positive number")
    if _is_number(start) and _is_number(end) and start >= end:
        errors.append(f"lyric line start_seconds ({start}) must be before end_seconds ({end})")

    return errors


def _overlaps(previous_end: float, current_start: float) -> bool:
    return current_start < previous_end


def validate_timeline_schema(data: dict) -> list[str]:
    """Structural validation of every section/beat/lyric_line, plus
    timeline-level semantic checks (chronological order, no overlaps)
    that no single item's own validator can see on its own."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["timeline must be a JSON object"]

    if "master_song_id" not in data or data["master_song_id"] in (None, ""):
        errors.append("missing required field: master_song_id")
    elif not isinstance(data["master_song_id"], str):
        errors.append("master_song_id must be a non-empty string")

    sections = data.get("sections", [])
    if not isinstance(sections, list):
        errors.append("sections must be a list")
        sections = []
    beats = data.get("beats", [])
    if not isinstance(beats, list):
        errors.append("beats must be a list")
        beats = []
    lyric_lines = data.get("lyric_lines", [])
    if not isinstance(lyric_lines, list):
        errors.append("lyric_lines must be a list")
        lyric_lines = []

    for index, section in enumerate(sections):
        errors.extend(f"sections[{index}]: {error}" for error in validate_section_schema(section))
    for index, beat in enumerate(beats):
        errors.extend(f"beats[{index}]: {error}" for error in validate_beat_schema(beat))
    for index, lyric_line in enumerate(lyric_lines):
        errors.extend(f"lyric_lines[{index}]: {error}" for error in validate_lyric_line_schema(lyric_line))

    if errors:
        return errors

    ordered_sections = sorted(sections, key=lambda item: item["start_seconds"])
    for previous, current in zip(ordered_sections, ordered_sections[1:]):
        if _overlaps(previous["end_seconds"], current["start_seconds"]):
            errors.append(
                f"sections {previous['id']!r} and {current['id']!r} overlap "
                f"({previous['end_seconds']} > {current['start_seconds']})"
            )

    ordered_lyric_lines = sorted(lyric_lines, key=lambda item: item["start_seconds"])
    for previous, current in zip(ordered_lyric_lines, ordered_lyric_lines[1:]):
        if _overlaps(previous["end_seconds"], current["start_seconds"]):
            errors.append(
                f"lyric lines {previous['id']!r} and {current['id']!r} overlap "
                f"({previous['end_seconds']} > {current['start_seconds']})"
            )

    ordered_beat_times = [beat["time"] for beat in sorted(beats, key=lambda item: item["index"])]
    if ordered_beat_times != sorted(ordered_beat_times):
        errors.append("beats must be in non-decreasing time order when sorted by index")

    return errors
