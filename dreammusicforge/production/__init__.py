"""DreamMusicForge Film Compiler -- production package (Release 0.4).

Public API:

    from dreammusicforge.production import (
        SemanticEvent, Sequence, Shot, ShotTiming, ShotPurpose,
        ShotRequirements, ShotContinuity, ProductionGraph,
        generate_sequence_id, is_valid_sequence_id,
        generate_semantic_event_id, is_valid_semantic_event_id,
        generate_shot_id, is_valid_shot_id,
        generate_graph_id, is_valid_graph_id,
        validate_sequence_schema, validate_semantic_event_schema,
        validate_shot_schema, validate_production_graph_schema,
        build_sequence, build_semantic_event, build_shot,
        assemble_production_graph,
        resolve_camera_language, resolve_color_language,
        ProductionGraphValidationError,
    )

Everything else in the full spec (Renderer Capability Atlas, Video
Slicer, provider compilers, verification, repair, assembly, ...) is
later releases and is not present here.
"""
from __future__ import annotations

from .builder import (
    assemble_production_graph, build_semantic_event, build_sequence, build_shot,
    resolve_camera_language, resolve_color_language,
)
from .errors import ProductionGraphValidationError
from .ids import (
    generate_graph_id, generate_semantic_event_id, generate_sequence_id, generate_shot_id,
    is_valid_graph_id, is_valid_semantic_event_id, is_valid_sequence_id, is_valid_shot_id,
)
from .models import (
    ProductionGraph, SemanticEvent, Sequence, Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming,
)
from .schema import (
    validate_production_graph_schema, validate_semantic_event_schema, validate_sequence_schema,
    validate_shot_schema,
)

__all__ = [
    "ProductionGraph", "ProductionGraphValidationError", "SemanticEvent", "Sequence", "Shot",
    "ShotContinuity", "ShotPurpose", "ShotRequirements", "ShotTiming", "assemble_production_graph",
    "build_semantic_event", "build_sequence", "build_shot", "generate_graph_id",
    "generate_semantic_event_id", "generate_sequence_id", "generate_shot_id", "is_valid_graph_id",
    "is_valid_semantic_event_id", "is_valid_sequence_id", "is_valid_shot_id",
    "resolve_camera_language", "resolve_color_language",
    "validate_production_graph_schema", "validate_semantic_event_schema", "validate_sequence_schema",
    "validate_shot_schema",
]
