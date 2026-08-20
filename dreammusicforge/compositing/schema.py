"""CompositeLayer / CompositeResult JSON schema contracts.

Same dependency-free, dict-shaped, hand-walked convention as every
sibling package's schema.py -- no `jsonschema` package. Each
validate_*_schema() function returns every error found, not just the
first; empty list means valid.
"""
from __future__ import annotations

import re

from .ids import is_valid_composite_id
from .models import LAYER_TYPES, MASK_TYPES

_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_sha256_hex(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256_HEX_PATTERN.match(value))


def validate_composite_layer_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["composite_layer must be a JSON object"]

    for field_name in ("layer_type", "source_file"):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if data["layer_type"] not in LAYER_TYPES:
        errors.append(f"composite_layer layer_type must be one of {LAYER_TYPES}, got {data['layer_type']!r}")
    if not _is_non_empty_str(data["source_file"]):
        errors.append("composite_layer source_file must be a non-empty string")

    mask_type = data.get("mask_type", "none")
    if mask_type not in MASK_TYPES:
        errors.append(f"composite_layer mask_type must be one of {MASK_TYPES}, got {mask_type!r}")
    if mask_type == "chromakey" and not _is_non_empty_str(data.get("chroma_color")):
        errors.append("composite_layer mask_type is 'chromakey' but chroma_color is missing")

    for field_name in ("chroma_similarity", "chroma_blend"):
        if field_name in data and not (0.0 <= float(data[field_name]) <= 1.0 if _is_number(data[field_name]) else False):
            errors.append(f"composite_layer {field_name} must be a number in [0.0, 1.0]")

    return errors


def validate_composite_result_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["composite_result must be a JSON object"]

    for field_name in (
        "id", "shot_id", "output_file", "output_hash", "width", "height", "duration_seconds",
    ):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not is_valid_composite_id(data["id"]):
        errors.append(f"composite_result id {data['id']!r} does not match the COMPOSITE-* format")
    for field_name in ("shot_id", "output_file"):
        if not _is_non_empty_str(data[field_name]):
            errors.append(f"composite_result {field_name} must be a non-empty string")
    if not _is_sha256_hex(data["output_hash"]):
        errors.append("composite_result output_hash must be a 64-character lowercase hex sha256 digest")

    for field_name in ("width", "height"):
        value = data[field_name]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"composite_result {field_name} must be a positive integer")

    duration = data["duration_seconds"]
    if not _is_number(duration) or duration <= 0:
        errors.append("composite_result duration_seconds must be a positive number")

    layers = data.get("layers", [])
    if not isinstance(layers, list) or len(layers) < 2:
        errors.append("composite_result layers must be a list with at least a background and a foreground layer")
        layers = []
    else:
        layer_types = [layer.get("layer_type") if isinstance(layer, dict) else None for layer in layers]
        if "background" not in layer_types:
            errors.append("composite_result layers must include exactly one 'background' layer")
        if "foreground" not in layer_types:
            errors.append("composite_result layers must include exactly one 'foreground' layer")
    for index, layer in enumerate(layers):
        errors.extend(f"layers[{index}]: {error}" for error in validate_composite_layer_schema(layer))

    return errors
