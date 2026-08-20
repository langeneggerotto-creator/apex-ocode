"""RunwayProfile / RunwayPackage JSON schema contracts.

Same dependency-free, dict-shaped, hand-walked convention as every
sibling package's schema.py -- no `jsonschema` package. Each
validate_*_schema() function returns every error found, not just the
first; empty list means valid.
"""
from __future__ import annotations

from .ids import is_valid_runway_package_id
from .models import RUNWAY_MODES


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_runway_profile_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["runway_profile must be a JSON object"]

    if not _is_non_empty_str(data.get("model")):
        errors.append("runway_profile model must be a non-empty string")

    max_duration = data.get("max_duration_seconds", 10.0)
    if not _is_number(max_duration) or max_duration <= 0:
        errors.append("runway_profile max_duration_seconds must be a positive number")

    supported_modes = data.get("supported_modes", RUNWAY_MODES)
    if not isinstance(supported_modes, (list, tuple)) or not supported_modes:
        errors.append("runway_profile supported_modes must be a non-empty list")
    else:
        unknown = [mode for mode in supported_modes if mode not in RUNWAY_MODES]
        if unknown:
            errors.append(f"runway_profile supported_modes contains unknown modes {unknown}, expected a subset of {RUNWAY_MODES}")

    durations = data.get("supported_durations_seconds", [])
    if durations and (not isinstance(durations, (list, tuple)) or not all(_is_number(d) and d > 0 for d in durations)):
        errors.append("runway_profile supported_durations_seconds must be a list of positive numbers")

    ratios = data.get("supported_ratios", [])
    if ratios and (not isinstance(ratios, (list, tuple)) or not all(_is_non_empty_str(r) for r in ratios)):
        errors.append("runway_profile supported_ratios must be a list of non-empty strings")

    return errors


def validate_runway_package_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["runway_package must be a JSON object"]

    for field_name in (
        "id", "render_task_id", "shot_id", "mode", "model", "prompt_text", "duration_seconds", "ratio",
    ):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not is_valid_runway_package_id(data["id"]):
        errors.append(f"runway_package id {data['id']!r} does not match the RUNWAY-* format")
    for field_name in ("render_task_id", "shot_id", "prompt_text", "ratio", "model"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"runway_package {field_name} must be a non-empty string")

    if data["mode"] not in RUNWAY_MODES:
        errors.append(f"runway_package mode must be one of {RUNWAY_MODES}, got {data['mode']!r}")

    duration = data["duration_seconds"]
    if not _is_number(duration) or duration <= 0:
        errors.append("runway_package duration_seconds must be a positive number")

    if data["mode"] == "image_to_video" and not _is_non_empty_str(data.get("prompt_image")):
        errors.append("runway_package mode is 'image_to_video' but prompt_image is missing")

    seed = data.get("seed")
    if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool) or seed < 0):
        errors.append("runway_package seed, if present, must be a non-negative integer")

    negative_prompt = data.get("negative_prompt")
    if negative_prompt is not None and not _is_non_empty_str(negative_prompt):
        errors.append("runway_package negative_prompt, if present, must be a non-empty string or null")

    if "audio" in data and not isinstance(data["audio"], bool):
        errors.append("runway_package audio must be a boolean")

    reference_manifest = data.get("reference_manifest", [])
    if not isinstance(reference_manifest, list) or not all(_is_non_empty_str(item) for item in reference_manifest):
        errors.append("runway_package reference_manifest must be a list of non-empty strings")

    return errors
