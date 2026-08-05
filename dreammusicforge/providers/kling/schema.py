"""KlingProfile / KlingPackage JSON schema contracts.

Same dependency-free, dict-shaped, hand-walked convention as every
sibling package's schema.py -- no `jsonschema` package. Each
validate_*_schema() function returns every error found, not just the
first; empty list means valid.
"""
from __future__ import annotations

from .ids import is_valid_kling_package_id
from .models import KLING_MODES


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_kling_profile_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["kling_profile must be a JSON object"]

    if "max_duration_seconds" not in data or data["max_duration_seconds"] in (None, ""):
        errors.append("missing required field: max_duration_seconds")
    if errors:
        return errors

    max_duration = data["max_duration_seconds"]
    if not _is_number(max_duration) or max_duration <= 0:
        errors.append("max_duration_seconds must be a positive number")

    supported_modes = data.get("supported_modes", KLING_MODES)
    if not isinstance(supported_modes, (list, tuple)) or not supported_modes:
        errors.append("supported_modes must be a non-empty list")
    else:
        unknown = [mode for mode in supported_modes if mode not in KLING_MODES]
        if unknown:
            errors.append(f"supported_modes contains unknown modes {unknown}, expected a subset of {KLING_MODES}")

    return errors


def validate_kling_package_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["kling_package must be a JSON object"]

    for field_name in (
        "id", "render_task_id", "shot_id", "mode", "duration_seconds",
        "duration_limit_seconds", "prompt", "negative_prompt", "reference_manifest",
    ):
        if field_name not in data or data[field_name] in (None, "", []):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not is_valid_kling_package_id(data["id"]):
        errors.append(f"kling_package id {data['id']!r} does not match the KLING-* format")
    for field_name in ("render_task_id", "shot_id", "prompt"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"kling_package {field_name} must be a non-empty string")

    if data["mode"] not in KLING_MODES:
        errors.append(f"kling_package mode must be one of {KLING_MODES}, got {data['mode']!r}")

    duration = data["duration_seconds"]
    limit = data["duration_limit_seconds"]
    if not _is_number(duration) or duration <= 0:
        errors.append("kling_package duration_seconds must be a positive number")
    if not _is_number(limit) or limit <= 0:
        errors.append("kling_package duration_limit_seconds must be a positive number")
    if _is_number(duration) and _is_number(limit) and duration > limit:
        errors.append(f"kling_package duration_seconds ({duration}) exceeds duration_limit_seconds ({limit})")

    negative_prompt = data["negative_prompt"]
    if not isinstance(negative_prompt, list) or not all(_is_non_empty_str(item) for item in negative_prompt):
        errors.append("negative_prompt must be a non-empty list of non-empty strings")

    reference_manifest = data["reference_manifest"]
    if not isinstance(reference_manifest, list) or not all(_is_non_empty_str(item) for item in reference_manifest):
        errors.append("reference_manifest must be a non-empty list of non-empty strings")

    return errors
