"""Identifier generation and validation for Release 0.4's new entity
types (Sequence, SemanticEvent, Shot, ProductionGraph), built on the
generic generate_id()/is_valid_id() core.ids added in Release 0.2 --
same pattern as music/ids.py and genome/ids.py.

Prefixes match spec section 6.7/6.8's example ids (SEM-014, SHOT-021,
SEQ-004) and section 6.1's production_graph_id example (GRAPH-001)."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

SEQUENCE_ID_PREFIX = "SEQ-"
SEMANTIC_EVENT_ID_PREFIX = "SEM-"
SHOT_ID_PREFIX = "SHOT-"
GRAPH_ID_PREFIX = "GRAPH-"


def generate_sequence_id() -> str:
    return generate_id(SEQUENCE_ID_PREFIX)


def is_valid_sequence_id(value: object) -> bool:
    return is_valid_id(value, SEQUENCE_ID_PREFIX)


def generate_semantic_event_id() -> str:
    return generate_id(SEMANTIC_EVENT_ID_PREFIX)


def is_valid_semantic_event_id(value: object) -> bool:
    return is_valid_id(value, SEMANTIC_EVENT_ID_PREFIX)


def generate_shot_id() -> str:
    return generate_id(SHOT_ID_PREFIX)


def is_valid_shot_id(value: object) -> bool:
    return is_valid_id(value, SHOT_ID_PREFIX)


def generate_graph_id() -> str:
    return generate_id(GRAPH_ID_PREFIX)


def is_valid_graph_id(value: object) -> bool:
    return is_valid_id(value, GRAPH_ID_PREFIX)
