"""Identifier generation and validation for Release 0.14's
FinishingResult, built on the generic generate_id()/is_valid_id()
core.ids added in Release 0.2 -- same pattern as every sibling
package's ids.py."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

FINISHING_RESULT_ID_PREFIX = "FINISHING-"


def generate_finishing_result_id() -> str:
    return generate_id(FINISHING_RESULT_ID_PREFIX)


def is_valid_finishing_result_id(value: object) -> bool:
    return is_valid_id(value, FINISHING_RESULT_ID_PREFIX)
