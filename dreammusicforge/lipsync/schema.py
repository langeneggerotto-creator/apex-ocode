"""LipSyncRequest / LipSyncResult JSON schema contracts.

Same dependency-free, dict-shaped, hand-walked convention as every
sibling package's schema.py -- no `jsonschema` package. Each
validate_*_schema() function returns every error found, not just the
first; empty list means valid.
"""
from __future__ import annotations

from .ids import is_valid_lip_sync_request_id
from .models import LIP_SYNC_RESULT_STATUSES


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_lip_sync_request_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["lip_sync_request must be a JSON object"]

    for field_name in (
        "id", "shot_id", "candidate_id", "source_file", "audio_window_file",
        "audio_start_seconds", "audio_end_seconds",
    ):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not is_valid_lip_sync_request_id(data["id"]):
        errors.append(f"lip_sync_request id {data['id']!r} does not match the LIPSYNC-* format")
    for field_name in ("shot_id", "candidate_id", "source_file", "audio_window_file"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"lip_sync_request {field_name} must be a non-empty string")

    start, end = data["audio_start_seconds"], data["audio_end_seconds"]
    if not _is_number(start) or start < 0:
        errors.append("lip_sync_request audio_start_seconds must be a non-negative number")
    if not _is_number(end) or end <= 0:
        errors.append("lip_sync_request audio_end_seconds must be a positive number")
    if _is_number(start) and _is_number(end) and start >= end:
        errors.append(f"lip_sync_request audio_start_seconds ({start}) must be before audio_end_seconds ({end})")

    return errors


def validate_lip_sync_result_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["lip_sync_result must be a JSON object"]

    for field_name in ("request_id", "status", "reason"):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not _is_non_empty_str(data["request_id"]):
        errors.append("lip_sync_result request_id must be a non-empty string")
    if data["status"] not in LIP_SYNC_RESULT_STATUSES:
        errors.append(f"lip_sync_result status must be one of {LIP_SYNC_RESULT_STATUSES}, got {data['status']!r}")
    if not _is_non_empty_str(data["reason"]):
        errors.append("lip_sync_result reason must be a non-empty string")

    output_file = data.get("output_file")
    if output_file is not None and not _is_non_empty_str(output_file):
        errors.append("lip_sync_result output_file, if present, must be a non-empty string or null")
    if data["status"] == "applied" and not output_file:
        errors.append("lip_sync_result status is 'applied' but output_file is missing -- an applied result must produce a file")

    return errors
