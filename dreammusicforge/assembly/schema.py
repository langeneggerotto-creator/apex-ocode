"""Transition / AssembledClip / ExportManifest JSON schema contracts.

Same dependency-free, dict-shaped, hand-walked convention as every
sibling package's schema.py -- no `jsonschema` package. Each
validate_*_schema() function returns every error found, not just the
first; empty list means valid.
"""
from __future__ import annotations

import re

from .ids import is_valid_export_id
from .models import TRANSITION_TYPES

_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_sha256_hex(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256_HEX_PATTERN.match(value))


def validate_transition_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["transition must be a JSON object"]

    for field_name in (
        "source_shot_id", "destination_shot_id", "transition_type", "duration_seconds",
        "musical_anchor", "visual_bridge", "semantic_purpose",
    ):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    for field_name in ("source_shot_id", "destination_shot_id", "musical_anchor", "visual_bridge", "semantic_purpose"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"transition {field_name} must be a non-empty string")

    if data["transition_type"] not in TRANSITION_TYPES:
        errors.append(f"transition_type must be one of {TRANSITION_TYPES}, got {data['transition_type']!r}")

    duration = data["duration_seconds"]
    if not _is_number(duration) or duration < 0:
        errors.append("transition duration_seconds must be a non-negative number")

    return errors


def validate_assembled_clip_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["assembled_clip must be a JSON object"]

    for field_name in ("candidate_id", "shot_id", "source_hash", "start_seconds_in_final", "normalized_duration_seconds"):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    for field_name in ("candidate_id", "shot_id"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"assembled_clip {field_name} must be a non-empty string")
    if not _is_sha256_hex(data["source_hash"]):
        errors.append("assembled_clip source_hash must be a 64-character lowercase hex sha256 digest")

    start = data["start_seconds_in_final"]
    duration = data["normalized_duration_seconds"]
    if not _is_number(start) or start < 0:
        errors.append("assembled_clip start_seconds_in_final must be a non-negative number")
    if not _is_number(duration) or duration <= 0:
        errors.append("assembled_clip normalized_duration_seconds must be a positive number")

    return errors


def validate_export_manifest_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["export_manifest must be a JSON object"]

    for field_name in (
        "id", "master_song_id", "master_song_hash", "output_file", "output_hash",
        "total_duration_seconds", "created_at",
    ):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not is_valid_export_id(data["id"]):
        errors.append(f"export_manifest id {data['id']!r} does not match the EXPORT-* format")
    for field_name in ("master_song_id", "output_file", "created_at"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"export_manifest {field_name} must be a non-empty string")
    for field_name in ("master_song_hash", "output_hash"):
        if not _is_sha256_hex(data[field_name]):
            errors.append(f"export_manifest {field_name} must be a 64-character lowercase hex sha256 digest")

    duration = data["total_duration_seconds"]
    if not _is_number(duration) or duration <= 0:
        errors.append("export_manifest total_duration_seconds must be a positive number")

    clips = data.get("clips", [])
    if not isinstance(clips, list) or not clips:
        errors.append("export_manifest clips must be a non-empty list")
        clips = []
    for index, clip in enumerate(clips):
        errors.extend(f"clips[{index}]: {error}" for error in validate_assembled_clip_schema(clip))

    transitions = data.get("transitions", [])
    if not isinstance(transitions, list):
        errors.append("export_manifest transitions, if present, must be a list")
        transitions = []
    for index, transition in enumerate(transitions):
        errors.extend(f"transitions[{index}]: {error}" for error in validate_transition_schema(transition))

    if isinstance(clips, list) and len(clips) >= 2:
        # A `dissolve` transition deliberately makes its two adjacent
        # clips overlap in the final timeline (that's what a crossfade
        # is), so overlap alone isn't an error -- only overlap that no
        # declared dissolve transition explains is. The 0.5s tolerance
        # absorbs float/frame-rounding drift between the Transition's
        # declared duration_seconds and ffmpeg's actual re-encoded
        # timing, without being loose enough to miss a real bug.
        dissolve_durations_by_shot_pair = {
            (t["source_shot_id"], t["destination_shot_id"]): t["duration_seconds"]
            for t in transitions if isinstance(t, dict) and t.get("transition_type") == "dissolve"
        }
        overlap_tolerance_seconds = 0.5
        ordered = sorted(clips, key=lambda item: item.get("start_seconds_in_final", 0))
        for previous, current in zip(ordered, ordered[1:]):
            previous_end = previous["start_seconds_in_final"] + previous["normalized_duration_seconds"]
            overlap = previous_end - current["start_seconds_in_final"]
            if overlap <= 0:
                continue
            expected_overlap = dissolve_durations_by_shot_pair.get((previous["shot_id"], current["shot_id"]))
            if expected_overlap is None or abs(overlap - expected_overlap) > overlap_tolerance_seconds:
                errors.append(
                    f"clips {previous['candidate_id']!r} and {current['candidate_id']!r} overlap in the final "
                    f"timeline ({previous_end} > {current['start_seconds_in_final']}) with no matching dissolve "
                    "transition to explain it"
                )

    return errors
