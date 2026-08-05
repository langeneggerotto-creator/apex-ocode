"""RendererCapability / RendererCapabilityProfile JSON schema
contracts.

Same dependency-free, dict-shaped, hand-walked convention as
core/schema.py, music/schema.py, genome/schema.py, and
production/schema.py -- no `jsonschema` package. Each
validate_*_schema() function returns every error found, not just the
first; empty list means valid.
"""
from __future__ import annotations

from .models import CAPABILITY_STATUSES


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_capability_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["capability must be a JSON object"]

    for field_name in ("name", "status"):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not _is_non_empty_str(data["name"]):
        errors.append("capability name must be a non-empty string")
    if data["status"] not in CAPABILITY_STATUSES:
        errors.append(f"capability status must be one of {CAPABILITY_STATUSES}, got {data['status']!r}")

    evidence = data.get("evidence")
    if evidence is not None and not _is_non_empty_str(evidence):
        errors.append("capability evidence, if present, must be a non-empty string or null")

    return errors


def validate_capability_profile_schema(data: dict) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["renderer_capability_profile must be a JSON object"]

    for field_name in ("provider", "max_duration_seconds", "max_character_count", "supported_camera_motions"):
        if field_name not in data or data[field_name] in (None, "", []):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not _is_non_empty_str(data["provider"]):
        errors.append("provider must be a non-empty string")

    max_duration = data["max_duration_seconds"]
    if not _is_number(max_duration) or max_duration <= 0:
        errors.append("max_duration_seconds must be a positive number")

    max_characters = data["max_character_count"]
    if not isinstance(max_characters, int) or isinstance(max_characters, bool) or max_characters <= 0:
        errors.append("max_character_count must be a positive integer")

    camera_motions = data["supported_camera_motions"]
    if not isinstance(camera_motions, list) or not camera_motions or not all(_is_non_empty_str(item) for item in camera_motions):
        errors.append("supported_camera_motions must be a non-empty list of non-empty strings")

    capabilities = data.get("capabilities", [])
    if not isinstance(capabilities, list):
        errors.append("capabilities, if present, must be a list")
        capabilities = []

    for index, capability in enumerate(capabilities):
        errors.extend(f"capabilities[{index}]: {error}" for error in validate_capability_schema(capability))

    if not errors:
        names = [capability["name"] for capability in capabilities]
        seen: set = set()
        duplicates: list = []
        for name in names:
            if name in seen and name not in duplicates:
                duplicates.append(name)
            seen.add(name)
        if duplicates:
            errors.append(f"capability names must be unique within a profile, duplicated: {duplicates}")

    return errors
