"""OperatorReport JSON schema contract.

Same dependency-free, dict-shaped, hand-walked convention as every
sibling package's schema.py -- no `jsonschema` package. Delegates each
nested item to its own package's already-established validator
(repair/assembly/finishing) rather than re-implementing their rules --
same "don't duplicate a validator that already exists" discipline
production/schema.py applies to genome id formats.
"""
from __future__ import annotations

from ..assembly.schema import validate_export_manifest_schema
from ..finishing.schema import validate_finishing_result_schema
from ..repair.schema import validate_verification_result_schema
from .ids import is_valid_operator_report_id


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def validate_operator_report_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["operator_report must be a JSON object"]

    for field_name in ("id", "generated_at"):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not is_valid_operator_report_id(data["id"]):
        errors.append(f"operator_report id {data['id']!r} does not match the REPORT-* format")
    if not _is_non_empty_str(data["generated_at"]):
        errors.append("operator_report generated_at must be a non-empty string")

    for field_name, validator in (
        ("verification_results", validate_verification_result_schema),
        ("export_manifests", validate_export_manifest_schema),
        ("finishing_results", validate_finishing_result_schema),
    ):
        items = data.get(field_name, [])
        if not isinstance(items, list):
            errors.append(f"operator_report {field_name}, if present, must be a list")
            continue
        for index, item in enumerate(items):
            errors.extend(f"{field_name}[{index}]: {error}" for error in validator(item))

    return errors
