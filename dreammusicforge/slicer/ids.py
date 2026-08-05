"""Identifier generation and validation for Release 0.6's new entity
types (TemporalSlice, VisualLayer, MotionLayer, RenderTask), built on
the generic generate_id()/is_valid_id() core.ids added in Release 0.2 --
same pattern as music/ids.py, genome/ids.py, and production/ids.py.

RENDER_ID_PREFIX matches spec section 6.9's example id (RENDER-021-B)."""
from __future__ import annotations

from ..core.ids import generate_id, is_valid_id

SLICE_ID_PREFIX = "SLICE-"
LAYER_ID_PREFIX = "LAYER-"
RENDER_ID_PREFIX = "RENDER-"


def generate_slice_id() -> str:
    return generate_id(SLICE_ID_PREFIX)


def is_valid_slice_id(value: object) -> bool:
    return is_valid_id(value, SLICE_ID_PREFIX)


def generate_layer_id() -> str:
    return generate_id(LAYER_ID_PREFIX)


def is_valid_layer_id(value: object) -> bool:
    return is_valid_id(value, LAYER_ID_PREFIX)


def generate_render_task_id() -> str:
    return generate_id(RENDER_ID_PREFIX)


def is_valid_render_task_id(value: object) -> bool:
    return is_valid_id(value, RENDER_ID_PREFIX)
