"""Identifier generation and validation for Release 0.10's Defect,
built on the generic generate_id()/is_valid_id() core.ids added in
Release 0.2 -- same pattern as every sibling package's ids.py.

VerificationResult and RepairPlan don't get their own id prefix: spec
section 6.11's `verification_result` example is keyed by candidate_id
alone (no separate id field), and a RepairPlan only ever exists attached
to the VerificationResult that produced it -- inventing redundant ids
for either would be scope the worked example doesn't show."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

DEFECT_ID_PREFIX = "DEFECT-"


def generate_defect_id() -> str:
    return generate_id(DEFECT_ID_PREFIX)


def is_valid_defect_id(value: object) -> bool:
    return is_valid_id(value, DEFECT_ID_PREFIX)
