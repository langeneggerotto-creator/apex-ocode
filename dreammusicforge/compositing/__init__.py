"""DreamMusicForge Film Compiler -- compositing package (Release 0.13).

Not verified against the original spec's own text for this release --
see models.py's module docstring for why.

Public API:

    from dreammusicforge.compositing import (
        LAYER_TYPES, MASK_TYPES, EXECUTABLE_MASK_TYPES,
        CompositeLayer, CompositeResult,
        composite_layers, build_composite,
        validate_composite_layer_schema, validate_composite_result_schema,
        generate_composite_id, is_valid_composite_id,
        CompositingError,
    )
"""
from __future__ import annotations

from .builder import build_composite
from .errors import CompositingError
from .ids import generate_composite_id, is_valid_composite_id
from .models import EXECUTABLE_MASK_TYPES, LAYER_TYPES, MASK_TYPES, CompositeLayer, CompositeResult
from .pipeline import composite_layers
from .schema import validate_composite_layer_schema, validate_composite_result_schema

__all__ = [
    "EXECUTABLE_MASK_TYPES", "LAYER_TYPES", "MASK_TYPES", "CompositeLayer", "CompositeResult",
    "CompositingError", "build_composite", "composite_layers", "generate_composite_id",
    "is_valid_composite_id", "validate_composite_layer_schema", "validate_composite_result_schema",
]
