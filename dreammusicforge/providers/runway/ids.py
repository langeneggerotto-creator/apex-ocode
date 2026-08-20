"""Identifier generation and validation for this addition's
RunwayPackage, built on the generic generate_id()/is_valid_id()
core.ids added in Release 0.2 -- same pattern as every sibling
package's ids.py (including providers.kling's own KLING_PACKAGE_ID_PREFIX)."""
from __future__ import annotations

from ...core.ids import generate_id, is_valid_id

RUNWAY_PACKAGE_ID_PREFIX = "RUNWAY-"


def generate_runway_package_id() -> str:
    return generate_id(RUNWAY_PACKAGE_ID_PREFIX)


def is_valid_runway_package_id(value: object) -> bool:
    return is_valid_id(value, RUNWAY_PACKAGE_ID_PREFIX)
