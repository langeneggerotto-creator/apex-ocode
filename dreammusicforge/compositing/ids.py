"""Identifier generation and validation for Release 0.13's
CompositeResult, built on the generic generate_id()/is_valid_id()
core.ids added in Release 0.2 -- same pattern as every sibling
package's ids.py."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

COMPOSITE_ID_PREFIX = "COMPOSITE-"


def generate_composite_id() -> str:
    return generate_id(COMPOSITE_ID_PREFIX)


def is_valid_composite_id(value: object) -> bool:
    return is_valid_id(value, COMPOSITE_ID_PREFIX)
