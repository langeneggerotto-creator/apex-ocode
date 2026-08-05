"""Sequence / SemanticEvent / Shot / ProductionGraph JSON schema
contracts.

Same dependency-free, dict-shaped, hand-walked convention as
core/schema.py, music/schema.py, and genome/schema.py -- no
`jsonschema` package. Each validate_*_schema() function returns every
error found, not just the first; empty list means valid.

validate_production_graph_schema() checks everything that's visible
from the production_graph dict alone: every nested Sequence/
SemanticEvent/Shot structurally, plus the cross-item checks Release
0.4's "dependencies" and "transition relationships" deliverables map to
-- no two shots overlap in time, every shot's sequence_id and
purpose.semantic_event_id resolve to a sequence/semantic_event actually
present in the same graph, and (spec Law 3.5's continuity requirement)
consecutive same-performer shots within the same sequence chain state
correctly (one shot's destination_state must equal the next shot's
inherited_state). It can only format-check requirements.performer_id/
costume_id/world_id (do they look like PERFORMER-*/COSTUME-*/WORLD-*
ids) -- checking they *exist* needs a FilmGenome, which isn't part of
this dict; that existence check lives in production/builder.py's
assemble_production_graph(), same division of responsibility as
genome/schema.py vs genome/builder.py.
"""
from __future__ import annotations

from ..genome.ids import is_valid_costume_id, is_valid_performer_id, is_valid_world_id
from .ids import is_valid_semantic_event_id, is_valid_sequence_id

ACCEPTANCE_SCORE_RANGE = (0.0, 100.0)


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_semantic_event_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["semantic_event must be a JSON object"]

    for field_name in ("id", "start_seconds", "end_seconds", "meaning", "transformation_from", "transformation_to"):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not _is_non_empty_str(data["id"]):
        errors.append("semantic_event id must be a non-empty string")

    start, end = data["start_seconds"], data["end_seconds"]
    if not _is_number(start) or start < 0:
        errors.append("semantic_event start_seconds must be a non-negative number")
    if not _is_number(end) or end <= 0:
        errors.append("semantic_event end_seconds must be a positive number")
    if _is_number(start) and _is_number(end) and start >= end:
        errors.append(f"semantic_event start_seconds ({start}) must be before end_seconds ({end})")

    for field_name in ("meaning", "transformation_from", "transformation_to"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"semantic_event {field_name} must be a non-empty string")

    for field_name in ("intended_viewer_inference", "required_visible_evidence"):
        value = data.get(field_name, [])
        if not isinstance(value, list) or not all(_is_non_empty_str(item) for item in value):
            errors.append(f"{field_name}, if present, must be a list of non-empty strings")

    return errors


def validate_sequence_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["sequence must be a JSON object"]

    for field_name in ("id", "song_section", "start_seconds", "end_seconds"):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not _is_non_empty_str(data["id"]):
        errors.append("sequence id must be a non-empty string")
    if not _is_non_empty_str(data["song_section"]):
        errors.append("sequence song_section must be a non-empty string")

    start, end = data["start_seconds"], data["end_seconds"]
    if not _is_number(start) or start < 0:
        errors.append("sequence start_seconds must be a non-negative number")
    if not _is_number(end) or end <= 0:
        errors.append("sequence end_seconds must be a positive number")
    if _is_number(start) and _is_number(end) and start >= end:
        errors.append(f"sequence start_seconds ({start}) must be before end_seconds ({end})")

    return errors


def validate_shot_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["shot must be a JSON object"]

    for field_name in ("id", "sequence_id", "timing", "purpose", "requirements", "continuity", "acceptance"):
        if field_name not in data or data[field_name] in (None, "", {}):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not _is_non_empty_str(data["id"]):
        errors.append("shot id must be a non-empty string")
    if not is_valid_sequence_id(data["sequence_id"]):
        errors.append(f"shot sequence_id {data['sequence_id']!r} does not match the SEQ-* format")

    timing = data["timing"]
    if not isinstance(timing, dict):
        errors.append("timing must be an object")
    else:
        for field_name in ("start_seconds", "end_seconds", "song_section"):
            if field_name not in timing or timing[field_name] in (None, ""):
                errors.append(f"timing.{field_name} is required")
        start, end = timing.get("start_seconds"), timing.get("end_seconds")
        if _is_number(start) and start < 0:
            errors.append("timing.start_seconds must be a non-negative number")
        if _is_number(end) and end <= 0:
            errors.append("timing.end_seconds must be a positive number")
        if _is_number(start) and _is_number(end) and start >= end:
            errors.append(f"timing.start_seconds ({start}) must be before timing.end_seconds ({end})")
        lyric_ids = timing.get("lyric_ids", [])
        if not isinstance(lyric_ids, list) or not all(_is_non_empty_str(item) for item in lyric_ids):
            errors.append("timing.lyric_ids, if present, must be a list of non-empty strings")

    purpose = data["purpose"]
    if not isinstance(purpose, dict):
        errors.append("purpose must be an object")
    else:
        if not is_valid_semantic_event_id(purpose.get("semantic_event_id")):
            errors.append(f"purpose.semantic_event_id {purpose.get('semantic_event_id')!r} does not match the SEM-* format")
        for field_name in ("narrative_function", "editorial_function"):
            if not _is_non_empty_str(purpose.get(field_name)):
                errors.append(f"purpose.{field_name} must be a non-empty string")

    requirements = data["requirements"]
    if not isinstance(requirements, dict):
        errors.append("requirements must be an object")
    else:
        if not is_valid_performer_id(requirements.get("performer_id")):
            errors.append(f"requirements.performer_id {requirements.get('performer_id')!r} does not match the PERFORMER-* format")
        if not is_valid_costume_id(requirements.get("costume_id")):
            errors.append(f"requirements.costume_id {requirements.get('costume_id')!r} does not match the COSTUME-* format")
        if not is_valid_world_id(requirements.get("world_id")):
            errors.append(f"requirements.world_id {requirements.get('world_id')!r} does not match the WORLD-* format")
        if not isinstance(requirements.get("lip_sync_required"), bool):
            errors.append("requirements.lip_sync_required must be a boolean")
        for field_name in ("choreography_complexity", "camera_motion"):
            if not _is_non_empty_str(requirements.get(field_name)):
                errors.append(f"requirements.{field_name} must be a non-empty string")
        character_count = requirements.get("character_count")
        if not isinstance(character_count, int) or isinstance(character_count, bool) or character_count <= 0:
            errors.append("requirements.character_count must be a positive integer")

    continuity = data["continuity"]
    if not isinstance(continuity, dict):
        errors.append("continuity must be an object")
    else:
        for field_name in ("inherited_state", "destination_state"):
            if not _is_non_empty_str(continuity.get(field_name)):
                errors.append(f"continuity.{field_name} must be a non-empty string")
        mutations = continuity.get("permitted_mutations", [])
        if not isinstance(mutations, list) or not all(_is_non_empty_str(item) for item in mutations):
            errors.append("continuity.permitted_mutations, if present, must be a list of non-empty strings")

    acceptance = data["acceptance"]
    if not isinstance(acceptance, dict) or not acceptance:
        errors.append("acceptance must be a non-empty object")
    else:
        low, high = ACCEPTANCE_SCORE_RANGE
        for key, value in acceptance.items():
            if not _is_number(value) or not (low < value <= high):
                errors.append(f"acceptance.{key} must be a number in ({low}, {high}], got {value!r}")

    return errors


def validate_production_graph_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["production_graph must be a JSON object"]

    for field_name in ("id", "film_genome_id"):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors
    if not _is_non_empty_str(data["id"]):
        errors.append("production_graph id must be a non-empty string")
    if not _is_non_empty_str(data["film_genome_id"]):
        errors.append("production_graph film_genome_id must be a non-empty string")

    sequences = data.get("sequences", [])
    if not isinstance(sequences, list):
        errors.append("sequences must be a list")
        sequences = []
    semantic_events = data.get("semantic_events", [])
    if not isinstance(semantic_events, list):
        errors.append("semantic_events must be a list")
        semantic_events = []
    shots = data.get("shots", [])
    if not isinstance(shots, list):
        errors.append("shots must be a list")
        shots = []

    for index, sequence in enumerate(sequences):
        errors.extend(f"sequences[{index}]: {error}" for error in validate_sequence_schema(sequence))
    for index, event in enumerate(semantic_events):
        errors.extend(f"semantic_events[{index}]: {error}" for error in validate_semantic_event_schema(event))
    for index, shot in enumerate(shots):
        errors.extend(f"shots[{index}]: {error}" for error in validate_shot_schema(shot))

    if errors:
        return errors

    sequence_ids = {sequence["id"] for sequence in sequences}
    semantic_event_ids = {event["id"] for event in semantic_events}

    for shot in shots:
        if shot["sequence_id"] not in sequence_ids:
            errors.append(f"shot {shot['id']!r} references sequence_id {shot['sequence_id']!r}, which is not in this graph's sequences")
        semantic_event_id = shot["purpose"]["semantic_event_id"]
        if semantic_event_id not in semantic_event_ids:
            errors.append(f"shot {shot['id']!r} references semantic_event_id {semantic_event_id!r}, which is not in this graph's semantic_events")

    ordered_shots = sorted(shots, key=lambda item: item["timing"]["start_seconds"])
    for previous, current in zip(ordered_shots, ordered_shots[1:]):
        if current["timing"]["start_seconds"] < previous["timing"]["end_seconds"]:
            errors.append(
                f"shots {previous['id']!r} and {current['id']!r} overlap in time "
                f"({previous['timing']['end_seconds']} > {current['timing']['start_seconds']})"
            )

    shots_by_sequence: dict[str, list[dict]] = {}
    for shot in ordered_shots:
        shots_by_sequence.setdefault(shot["sequence_id"], []).append(shot)

    for sequence_shots in shots_by_sequence.values():
        by_performer: dict[str, list[dict]] = {}
        for shot in sequence_shots:
            by_performer.setdefault(shot["requirements"]["performer_id"], []).append(shot)
        for performer_shots in by_performer.values():
            for previous, current in zip(performer_shots, performer_shots[1:]):
                if previous["continuity"]["destination_state"] != current["continuity"]["inherited_state"]:
                    errors.append(
                        f"shot {current['id']!r} breaks state inheritance from {previous['id']!r}: "
                        f"expected inherited_state {previous['continuity']['destination_state']!r}, "
                        f"got {current['continuity']['inherited_state']!r}"
                    )

    return errors
