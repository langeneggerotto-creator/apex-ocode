"""DMF-IR v1 validator.

Two layers, matching schema.py's split:

- validate_schema(data): structural checks -- every required field is
  present at every level, walked directly from DMF_IR_SCHEMA so the schema
  and its enforcement can't silently drift apart.
- validate_semantics(project): the business rules (state inheritance,
  timeline coherence, referential integrity, continuity-mode legality).
  Deliberately a strict superset of runtime.validate_project()'s checks --
  see the "new in DMF-IR" checks below, none of which
  dreammusicforge/examples/begin_again_project.json violates.

validate(data) runs both in order and is what compiler.compile() calls.
Fails closed: any schema error stops before semantic validation runs at
all, since semantic validation assumes the shape schema.py guarantees.
"""
from __future__ import annotations

from ..runtime import ValidationResult
from .models import DMFProject, parse_project
from .schema import CONTINUITY_MODES, DMF_IR_SCHEMA, PREVIOUS_CLIP_REQUIRED_MODES


def validate_schema(data: dict) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return ValidationResult(False, ["project must be a JSON object"], warnings)

    for field_name in DMF_IR_SCHEMA["required"]:
        if field_name not in data:
            errors.append(f"missing required top-level field: {field_name}")
    if errors:
        return ValidationResult(False, errors, warnings)

    for field_name, spec in DMF_IR_SCHEMA["properties"].items():
        if field_name not in data:
            continue  # already covered above, or optional (schema_version)
        value = data[field_name]

        if spec.get("type") == "object":
            if not isinstance(value, dict):
                errors.append(f"{field_name} must be an object")
                continue
            for required_field in spec.get("required", []):
                if required_field not in value:
                    errors.append(f"{field_name}.{required_field} is required")

        elif spec.get("type") == "array":
            if not isinstance(value, list):
                errors.append(f"{field_name} must be a list")
                continue
            min_items = spec.get("minItems")
            if min_items and len(value) < min_items:
                noun = "entry" if min_items == 1 else "entries"
                errors.append(f"{field_name} must contain at least {min_items} {noun}")
            item_required = spec.get("items", {}).get("required", [])
            for index, item in enumerate(value):
                if not isinstance(item, dict):
                    errors.append(f"{field_name}[{index}] must be an object")
                    continue
                label = item.get("id", f"index {index}")
                for required_field in item_required:
                    if required_field not in item:
                        errors.append(f"{field_name}[{label}].{required_field} is required")

    return ValidationResult(not errors, errors, warnings)


def validate_semantics(project: DMFProject, max_clip_seconds: float = 15.0) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    characters = project.index_characters()
    worlds = project.index_worlds()
    states = project.index_reality_states()
    semantics = project.index_semantic_events()
    music = project.index_music_events()
    checks = project.index_verification_contracts()

    clips = project.clips_in_order()
    previous_end = 0.0
    previous_destination: str | None = None

    for position, clip in enumerate(clips):
        cid = clip.id

        if clip.start < previous_end:
            errors.append(f"{cid} overlaps previous clip")
        if clip.duration_seconds <= 0:
            errors.append(f"{cid} has invalid duration")
        if clip.duration_seconds > max_clip_seconds:
            errors.append(f"{cid} exceeds provider duration limit")

        source = states.get(clip.source_state_id)
        destination = states.get(clip.destination_state_id)
        if source is None:
            errors.append(f"{cid} missing source state {clip.source_state_id}")
        elif source.timecode != clip.start:
            errors.append(
                f"{cid} source state {clip.source_state_id} timecode ({source.timecode}) "
                f"does not match clip start ({clip.start})"
            )
        if destination is None:
            errors.append(f"{cid} missing destination state {clip.destination_state_id}")
        elif destination.timecode != clip.end:
            errors.append(
                f"{cid} destination state {clip.destination_state_id} timecode ({destination.timecode}) "
                f"does not match clip end ({clip.end})"
            )

        if previous_destination is not None and clip.source_state_id != previous_destination:
            errors.append(f"{cid} breaks state inheritance")

        for event_id in clip.semantic_event_ids:
            event = semantics.get(event_id)
            if event is None:
                errors.append(f"{cid} missing semantic event {event_id}")
            elif event.end <= clip.start or event.start >= clip.end:
                errors.append(
                    f"{cid} semantic event {event_id} ({event.start}-{event.end}s) "
                    f"does not overlap the clip window ({clip.start}-{clip.end}s)"
                )

        for event_id in clip.music_event_ids:
            event = music.get(event_id)
            if event is None:
                errors.append(f"{cid} missing music event {event_id}")
            elif event.end <= clip.start or event.start >= clip.end:
                errors.append(
                    f"{cid} music event {event_id} ({event.start}-{event.end}s) "
                    f"does not overlap the clip window ({clip.start}-{clip.end}s)"
                )

        if clip.verification_contract_id not in checks:
            errors.append(f"{cid} missing verification contract")

        if clip.continuity_mode not in CONTINUITY_MODES:
            errors.append(f"{cid} uses unsupported continuity mode")
        elif clip.continuity_mode in PREVIOUS_CLIP_REQUIRED_MODES and position == 0:
            errors.append(
                f"{cid} uses continuity mode '{clip.continuity_mode}', which depends on a previous "
                f"clip's exported frame or video, but is first in the timeline"
            )

        if clip.total_actions > clip.maximum_actions:
            errors.append(f"{cid} exceeds maximum action count")

        for asset_id in clip.required_reference_assets:
            if asset_id not in characters and asset_id not in worlds:
                errors.append(f"{cid} required_reference_assets references unknown character/world '{asset_id}'")

        previous_end = clip.end
        previous_destination = clip.destination_state_id

    if clips:
        last_end = clips[-1].end
        if last_end != project.film.duration_seconds:
            errors.append(
                f"film.duration_seconds ({project.film.duration_seconds}) does not match "
                f"the last clip's end time ({last_end}) -- music is the master clock, so the "
                f"declared runtime and the actual timeline must agree"
            )

    music_sorted = sorted(project.music_events, key=lambda item: item.start)
    if music_sorted:
        cursor = 0.0
        for event in music_sorted:
            if event.start != cursor:
                errors.append(
                    f"music timeline has a gap or overlap before {event.id} "
                    f"(expected it to start at {cursor}, got {event.start})"
                )
            cursor = event.end
        if cursor != project.film.duration_seconds:
            errors.append(
                f"music timeline ends at {cursor}, which does not match film.duration_seconds "
                f"({project.film.duration_seconds})"
            )

    for contract in project.verification_contracts:
        if not (0 < contract.pass_threshold <= 1):
            errors.append(f"verification contract {contract.id} pass_threshold must be in (0, 1]")

    return ValidationResult(not errors, errors, warnings)


def validate(data: dict, max_clip_seconds: float = 15.0) -> ValidationResult:
    schema_result = validate_schema(data)
    if not schema_result.valid:
        return schema_result
    project = parse_project(data)
    return validate_semantics(project, max_clip_seconds=max_clip_seconds)
