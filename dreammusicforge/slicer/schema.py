"""TemporalSlice / VisualLayer / MotionLayer / RenderTask / SliceResult
JSON schema contracts.

Same dependency-free, dict-shaped, hand-walked convention as
core/schema.py and every sibling package's schema.py -- no
`jsonschema` package. Each validate_*_schema() function returns every
error found, not just the first; empty list means valid.
"""
from __future__ import annotations

from .ids import is_valid_render_task_id
from .models import SLICING_STRATEGIES


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_temporal_slice_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["temporal_slice must be a JSON object"]

    for field_name in ("id", "index", "start_seconds", "end_seconds"):
        if field_name not in data:
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not _is_non_empty_str(data["id"]):
        errors.append("temporal_slice id must be a non-empty string")
    index = data["index"]
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        errors.append("temporal_slice index must be a non-negative integer")

    start, end = data["start_seconds"], data["end_seconds"]
    if not _is_number(start) or start < 0:
        errors.append("temporal_slice start_seconds must be a non-negative number")
    if not _is_number(end) or end <= 0:
        errors.append("temporal_slice end_seconds must be a positive number")
    if _is_number(start) and _is_number(end) and start >= end:
        errors.append(f"temporal_slice start_seconds ({start}) must be before end_seconds ({end})")

    return errors


def validate_visual_layer_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["visual_layer must be a JSON object"]
    for field_name in ("id", "name"):
        if field_name not in data or not _is_non_empty_str(data.get(field_name)):
            errors.append(f"visual_layer {field_name} must be a non-empty string")
    return errors


def validate_motion_layer_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["motion_layer must be a JSON object"]
    for field_name in ("id", "name", "camera_motion"):
        if field_name not in data or not _is_non_empty_str(data.get(field_name)):
            errors.append(f"motion_layer {field_name} must be a non-empty string")
    return errors


def validate_render_task_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["render_task must be a JSON object"]

    for field_name in ("id", "shot_id", "slice_id", "provider", "duration_seconds"):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not is_valid_render_task_id(data["id"]):
        errors.append(f"render_task id {data['id']!r} does not match the RENDER-* format")
    for field_name in ("shot_id", "slice_id", "provider"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"render_task {field_name} must be a non-empty string")

    duration = data["duration_seconds"]
    if not _is_number(duration) or duration <= 0:
        errors.append("render_task duration_seconds must be a positive number")

    required_assets = data.get("required_assets", [])
    if not isinstance(required_assets, list) or not all(_is_non_empty_str(item) for item in required_assets):
        errors.append("required_assets must be a list of non-empty strings")

    for optional_field in ("mode", "prompt_file", "negative_prompt_file"):
        value = data.get(optional_field)
        if value is not None and not _is_non_empty_str(value):
            errors.append(f"render_task {optional_field}, if present, must be a non-empty string or null")

    return errors


def validate_slice_result_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["slice_result must be a JSON object"]

    for field_name in ("shot_id", "strategy"):
        if field_name not in data or not _is_non_empty_str(data.get(field_name)):
            errors.append(f"slice_result {field_name} must be a non-empty string")
    if errors:
        return errors

    if data["strategy"] not in SLICING_STRATEGIES:
        errors.append(f"slice_result strategy must be one of {SLICING_STRATEGIES}, got {data['strategy']!r}")

    render_tasks = data.get("render_tasks", [])
    if not isinstance(render_tasks, list):
        errors.append("render_tasks must be a list")
        render_tasks = []
    for index, task in enumerate(render_tasks):
        errors.extend(f"render_tasks[{index}]: {error}" for error in validate_render_task_schema(task))

    temporal_slices = data.get("temporal_slices", [])
    if not isinstance(temporal_slices, list):
        errors.append("temporal_slices must be a list")
        temporal_slices = []
    for index, item in enumerate(temporal_slices):
        errors.extend(f"temporal_slices[{index}]: {error}" for error in validate_temporal_slice_schema(item))

    if data["strategy"] == "external_production_required":
        if render_tasks:
            errors.append("external_production_required must not produce any render_tasks")
        if not data.get("fallback_plan"):
            errors.append("external_production_required requires a fallback_plan")
    else:
        if not render_tasks:
            errors.append(f"strategy {data['strategy']!r} must produce at least one render_task")

    return errors
