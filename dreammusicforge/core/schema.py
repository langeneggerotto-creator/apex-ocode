"""Project JSON schema contract.

Same convention as the sibling dreammusicforge module's schema files:
a plain, dependency-free Python dict in JSON-Schema-like shape, walked by
hand in validate_project_schema() rather than through the `jsonschema`
package -- no new dependency, and the contract stays inspectable as data.
"""
from __future__ import annotations

from .models import PROJECT_STATUSES

PROJECT_SCHEMA_VERSION = "0.1.0"

PROJECT_SCHEMA: dict = {
    "$id": "dreammusicforge/core/schema.py:PROJECT_SCHEMA",
    "schema_version": PROJECT_SCHEMA_VERSION,
    "type": "object",
    "required": [
        "id", "title", "version", "status", "aspect_ratio", "resolution",
        "frame_rate", "target_duration_seconds", "providers", "created_at", "updated_at",
    ],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "title": {"type": "string", "minLength": 1},
        "version": {"type": "string", "minLength": 1},
        "status": {"enum": sorted(PROJECT_STATUSES)},
        "aspect_ratio": {"type": "string", "minLength": 1},
        "resolution": {"type": "string", "minLength": 1},
        "frame_rate": {"type": "number", "exclusiveMinimum": 0},
        "target_duration_seconds": {"type": "number", "exclusiveMinimum": 0},
        "providers": {"type": "array", "items": {"type": "string"}},
        "master_song_id": {"type": ["string", "null"], "optional": True},
        "film_genome_id": {"type": ["string", "null"], "optional": True},
        "production_graph_id": {"type": ["string", "null"], "optional": True},
        "created_at": {"type": "string", "minLength": 1},
        "updated_at": {"type": "string", "minLength": 1},
    },
}


def validate_project_schema(data: dict) -> list[str]:
    """Structural + basic semantic checks. Returns every error found, not
    just the first -- empty list means valid. Does not check project id
    *format* (core.ids.validate_project_id owns that; kept separate so a
    malformed id and a missing field are reported as distinct, specific
    problems rather than conflated)."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["project must be a JSON object"]

    for field_name in PROJECT_SCHEMA["required"]:
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")

    if errors:
        return errors

    if not isinstance(data["id"], str) or not data["id"]:
        errors.append("id must be a non-empty string")
    if not isinstance(data["title"], str) or not data["title"]:
        errors.append("title must be a non-empty string")
    if not isinstance(data["version"], str) or not data["version"]:
        errors.append("version must be a non-empty string")

    if data["status"] not in PROJECT_STATUSES:
        errors.append(f"status must be one of {sorted(PROJECT_STATUSES)}, got {data['status']!r}")

    frame_rate = data.get("frame_rate")
    if not isinstance(frame_rate, (int, float)) or isinstance(frame_rate, bool) or frame_rate <= 0:
        errors.append("frame_rate must be a positive number")

    duration = data.get("target_duration_seconds")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
        errors.append("target_duration_seconds must be a positive number")

    providers = data.get("providers")
    if not isinstance(providers, list):
        errors.append("providers must be a list")
    elif not all(isinstance(p, str) and p for p in providers):
        errors.append("providers must be a list of non-empty strings")

    for optional_field in ("master_song_id", "film_genome_id", "production_graph_id"):
        value = data.get(optional_field)
        if value is not None and (not isinstance(value, str) or not value):
            errors.append(f"{optional_field}, if present, must be a non-empty string or null")

    return errors
