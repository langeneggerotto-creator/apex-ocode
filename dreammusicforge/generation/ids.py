"""Identifier generation and validation for Release 0.8's Candidate,
built on the generic generate_id()/is_valid_id() core.ids added in
Release 0.2 -- same pattern as every sibling package's ids.py.

CANDIDATE_ID_PREFIX matches spec section 6.10's example id
(CANDIDATE-021-B-003)."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

CANDIDATE_ID_PREFIX = "CANDIDATE-"


def generate_candidate_id() -> str:
    return generate_id(CANDIDATE_ID_PREFIX)


def is_valid_candidate_id(value: object) -> bool:
    return is_valid_id(value, CANDIDATE_ID_PREFIX)
