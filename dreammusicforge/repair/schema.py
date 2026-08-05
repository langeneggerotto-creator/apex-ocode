"""Defect / RepairPlan / VerificationResult JSON schema contracts.

Same dependency-free, dict-shaped, hand-walked convention as every
sibling package's schema.py -- no `jsonschema` package. Each
validate_*_schema() function returns every error found, not just the
first; empty list means valid.
"""
from __future__ import annotations

from .ids import is_valid_defect_id
from .models import DECISION_VALUES, SEVERITY_LEVELS


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_defect_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["defect must be a JSON object"]

    for field_name in ("id", "type", "severity", "location", "recommendations"):
        if field_name not in data or data[field_name] in (None, "", []):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not is_valid_defect_id(data["id"]):
        errors.append(f"defect id {data['id']!r} does not match the DEFECT-* format")
    if not _is_non_empty_str(data["type"]):
        errors.append("defect type must be a non-empty string")
    if data["severity"] not in SEVERITY_LEVELS:
        errors.append(f"defect severity must be one of {SEVERITY_LEVELS}, got {data['severity']!r}")

    location = data["location"]
    if not isinstance(location, dict) or not _is_non_empty_str(location.get("shot_id")):
        errors.append("defect location.shot_id must be a non-empty string")
    else:
        start, end = location.get("start"), location.get("end")
        if start is not None and not _is_number(start):
            errors.append("defect location.start, if present, must be a number")
        if end is not None and not _is_number(end):
            errors.append("defect location.end, if present, must be a number")
        if _is_number(start) and _is_number(end) and start >= end:
            errors.append(f"defect location.start ({start}) must be before location.end ({end})")

    recommendations = data["recommendations"]
    if not isinstance(recommendations, list) or not recommendations or not all(_is_non_empty_str(item) for item in recommendations):
        errors.append("defect recommendations must be a non-empty list of non-empty strings")

    return errors


def validate_repair_plan_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["repair_plan must be a JSON object"]

    for field_name in ("shot_id", "action"):
        if field_name not in data or not _is_non_empty_str(data.get(field_name)):
            errors.append(f"repair_plan {field_name} must be a non-empty string")

    preserve = data.get("preserve", [])
    if not isinstance(preserve, list) or not all(_is_non_empty_str(item) for item in preserve):
        errors.append("repair_plan preserve, if present, must be a list of non-empty strings")

    return errors


def validate_verification_result_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["verification_result must be a JSON object"]

    for field_name in ("candidate_id", "metrics", "critical_failures", "overall_score", "decision"):
        if field_name not in data:
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not _is_non_empty_str(data["candidate_id"]):
        errors.append("verification_result candidate_id must be a non-empty string")

    metrics = data["metrics"]
    if not isinstance(metrics, dict) or not metrics:
        errors.append("verification_result metrics must be a non-empty object")
    elif not all(_is_non_empty_str(name) and _is_number(score) for name, score in metrics.items()):
        errors.append("verification_result metrics must map non-empty names to numbers")

    critical_failures = data["critical_failures"]
    if not isinstance(critical_failures, list) or not all(_is_non_empty_str(item) for item in critical_failures):
        errors.append("verification_result critical_failures must be a list of non-empty strings")
    elif isinstance(metrics, dict):
        unknown = [name for name in critical_failures if name not in metrics]
        if unknown:
            errors.append(f"verification_result critical_failures references metrics not in metrics: {unknown}")

    if not _is_number(data["overall_score"]):
        errors.append("verification_result overall_score must be a number")

    if data["decision"] not in DECISION_VALUES:
        errors.append(f"verification_result decision must be one of {DECISION_VALUES}, got {data['decision']!r}")

    if isinstance(critical_failures, list):
        if data["decision"] == "reject" and not critical_failures:
            errors.append("verification_result decision is reject but critical_failures is empty")
        if data["decision"] == "accept" and critical_failures:
            errors.append("verification_result decision is accept but critical_failures is non-empty")

    defects = data.get("defects", [])
    if not isinstance(defects, list):
        errors.append("verification_result defects, if present, must be a list")
        defects = []
    for index, defect in enumerate(defects):
        errors.extend(f"defects[{index}]: {error}" for error in validate_defect_schema(defect))

    repair = data.get("repair")
    if data["decision"] == "reject" and repair is None:
        errors.append("verification_result decision is reject but repair is missing -- a rejected candidate must produce a bounded repair plan")
    if data["decision"] == "accept" and repair is not None:
        errors.append("verification_result decision is accept but repair is present")
    if repair is not None:
        errors.extend(f"repair: {error}" for error in validate_repair_plan_schema(repair))

    return errors
