"""Identifier generation and validation for Release 0.15's
OperatorReport, built on the generic generate_id()/is_valid_id()
core.ids added in Release 0.2 -- same pattern as every sibling
package's ids.py."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

OPERATOR_REPORT_ID_PREFIX = "REPORT-"


def generate_operator_report_id() -> str:
    return generate_id(OPERATOR_REPORT_ID_PREFIX)


def is_valid_operator_report_id(value: object) -> bool:
    return is_valid_id(value, OPERATOR_REPORT_ID_PREFIX)
