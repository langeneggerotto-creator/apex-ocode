"""LoudnessReport / ColorAdjustment / FinishingResult JSON schema
contracts.

Same dependency-free, dict-shaped, hand-walked convention as every
sibling package's schema.py -- no `jsonschema` package. Each
validate_*_schema() function returns every error found, not just the
first; empty list means valid.
"""
from __future__ import annotations

import re

from .ids import is_valid_finishing_result_id

_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_sha256_hex(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256_HEX_PATTERN.match(value))


def validate_loudness_report_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["loudness_report must be a JSON object"]

    for field_name in ("integrated_lufs", "true_peak_dbfs", "loudness_range_lu"):
        if field_name not in data or not _is_number(data[field_name]):
            errors.append(f"loudness_report {field_name} must be a number")

    if _is_number(data.get("loudness_range_lu")) and data["loudness_range_lu"] < 0:
        errors.append("loudness_report loudness_range_lu must be non-negative")

    return errors


def validate_color_adjustment_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["color_adjustment must be a JSON object"]

    for field_name in ("brightness", "contrast", "saturation"):
        if field_name in data and not _is_number(data[field_name]):
            errors.append(f"color_adjustment {field_name} must be a number")

    if _is_number(data.get("contrast")) and data["contrast"] < 0:
        errors.append("color_adjustment contrast must be non-negative")
    if _is_number(data.get("saturation")) and data["saturation"] < 0:
        errors.append("color_adjustment saturation must be non-negative")

    return errors


def validate_finishing_result_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["finishing_result must be a JSON object"]

    for field_name in (
        "id", "source_file", "output_file", "output_hash", "target_lufs",
        "measured_loudness", "color_adjustment", "duration_seconds",
    ):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not is_valid_finishing_result_id(data["id"]):
        errors.append(f"finishing_result id {data['id']!r} does not match the FINISHING-* format")
    for field_name in ("source_file", "output_file"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"finishing_result {field_name} must be a non-empty string")
    if not _is_sha256_hex(data["output_hash"]):
        errors.append("finishing_result output_hash must be a 64-character lowercase hex sha256 digest")
    if not _is_number(data["target_lufs"]):
        errors.append("finishing_result target_lufs must be a number")

    duration = data["duration_seconds"]
    if not _is_number(duration) or duration <= 0:
        errors.append("finishing_result duration_seconds must be a positive number")

    errors.extend(f"measured_loudness: {e}" for e in validate_loudness_report_schema(data["measured_loudness"]))
    errors.extend(f"color_adjustment: {e}" for e in validate_color_adjustment_schema(data["color_adjustment"]))

    return errors
