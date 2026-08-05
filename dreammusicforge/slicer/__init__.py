"""DreamMusicForge Film Compiler -- slicer package (Release 0.6).

Public API:

    from dreammusicforge.slicer import (
        RISK_FACTOR_NAMES, SLICING_STRATEGIES, EXPECTED_RENDER_OUTPUTS,
        RiskFactors, TemporalSlice, VisualLayer, MotionLayer, FallbackPlan,
        RenderTask, StrategyDecision, SliceResult,
        compute_risk_factors, select_strategy, slice_shot,
        validate_temporal_slice_schema, validate_visual_layer_schema,
        validate_motion_layer_schema, validate_render_task_schema,
        validate_slice_result_schema,
        generate_slice_id, is_valid_slice_id,
        generate_layer_id, is_valid_layer_id,
        generate_render_task_id, is_valid_render_task_id,
        SlicerValidationError,
    )

Everything else in the full spec (Kling Compiler, candidate intake,
verification, repair, assembly, ...) is later releases and is not
present here.
"""
from __future__ import annotations

from .builder import slice_shot
from .errors import SlicerValidationError
from .ids import (
    generate_layer_id, generate_render_task_id, generate_slice_id, is_valid_layer_id,
    is_valid_render_task_id, is_valid_slice_id,
)
from .models import (
    EXPECTED_RENDER_OUTPUTS, RISK_FACTOR_NAMES, SLICING_STRATEGIES, FallbackPlan, MotionLayer, RenderTask,
    RiskFactors, SliceResult, StrategyDecision, TemporalSlice, VisualLayer,
)
from .risk import compute_risk_factors
from .schema import (
    validate_motion_layer_schema, validate_render_task_schema, validate_slice_result_schema,
    validate_temporal_slice_schema, validate_visual_layer_schema,
)
from .strategy import select_strategy

__all__ = [
    "EXPECTED_RENDER_OUTPUTS", "FallbackPlan", "MotionLayer", "RenderTask",
    "RISK_FACTOR_NAMES", "RiskFactors", "SLICING_STRATEGIES", "SliceResult", "SlicerValidationError",
    "StrategyDecision", "TemporalSlice", "VisualLayer", "compute_risk_factors", "generate_layer_id",
    "generate_render_task_id", "generate_slice_id", "is_valid_layer_id", "is_valid_render_task_id",
    "is_valid_slice_id", "select_strategy", "slice_shot", "validate_motion_layer_schema",
    "validate_render_task_schema", "validate_slice_result_schema", "validate_temporal_slice_schema",
    "validate_visual_layer_schema",
]
