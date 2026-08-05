"""Identifier generation and validation for Release 0.7's KlingPackage,
built on the generic generate_id()/is_valid_id() core.ids added in
Release 0.2 -- same pattern as every sibling package's ids.py."""
from __future__ import annotations

from ...core.ids import generate_id, is_valid_id

KLING_PACKAGE_ID_PREFIX = "KLING-"


def generate_kling_package_id() -> str:
    return generate_id(KLING_PACKAGE_ID_PREFIX)


def is_valid_kling_package_id(value: object) -> bool:
    return is_valid_id(value, KLING_PACKAGE_ID_PREFIX)
