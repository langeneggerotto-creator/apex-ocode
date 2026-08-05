"""Candidate JSON schema contract.

Same dependency-free, dict-shaped, hand-walked convention as every
sibling package's schema.py -- no `jsonschema` package.
validate_candidate_schema() returns every error found, not just the
first; empty list means valid.
"""
from __future__ import annotations

import re

from .ids import is_valid_candidate_id
from .models import CANDIDATE_DECISIONS, CANDIDATE_VERIFICATION_STATUSES

_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_sha256_hex(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256_HEX_PATTERN.match(value))


def validate_candidate_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["candidate must be a JSON object"]

    for field_name in (
        "id", "render_task_id", "provider", "model_version", "file", "file_size_bytes",
        "prompt_hash", "output_hash", "imported_at",
    ):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not is_valid_candidate_id(data["id"]):
        errors.append(f"candidate id {data['id']!r} does not match the CANDIDATE-* format")
    for field_name in ("render_task_id", "provider", "model_version", "file", "imported_at"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"candidate {field_name} must be a non-empty string")

    file_size = data["file_size_bytes"]
    if not isinstance(file_size, int) or isinstance(file_size, bool) or file_size <= 0:
        errors.append("candidate file_size_bytes must be a positive integer")

    if not _is_sha256_hex(data["prompt_hash"]):
        errors.append("candidate prompt_hash must be a 64-character lowercase hex sha256 digest")
    if not _is_sha256_hex(data["output_hash"]):
        errors.append("candidate output_hash must be a 64-character lowercase hex sha256 digest")

    reference_hashes = data.get("reference_hashes", [])
    if not isinstance(reference_hashes, list) or not all(_is_sha256_hex(item) for item in reference_hashes):
        errors.append("candidate reference_hashes, if present, must be a list of sha256 hex digests")

    verification_status = data.get("verification_status", "pending")
    if verification_status not in CANDIDATE_VERIFICATION_STATUSES:
        errors.append(f"candidate verification_status must be one of {CANDIDATE_VERIFICATION_STATUSES}, got {verification_status!r}")

    decision = data.get("decision", "pending")
    if decision not in CANDIDATE_DECISIONS:
        errors.append(f"candidate decision must be one of {CANDIDATE_DECISIONS}, got {decision!r}")

    return errors
