"""Identifier generation and validation for Release 0.11's
ExportManifest, built on the generic generate_id()/is_valid_id()
core.ids added in Release 0.2 -- same pattern as every sibling
package's ids.py."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

EXPORT_ID_PREFIX = "EXPORT-"


def generate_export_id() -> str:
    return generate_id(EXPORT_ID_PREFIX)


def is_valid_export_id(value: object) -> bool:
    return is_valid_id(value, EXPORT_ID_PREFIX)
