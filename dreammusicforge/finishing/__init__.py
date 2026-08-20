"""DreamMusicForge Film Compiler -- finishing package (Release 0.14).

Not verified against the original spec's own text for this release --
see models.py's module docstring for why.

Public API:

    from dreammusicforge.finishing import (
        LoudnessReport, ColorAdjustment, FinishingResult,
        measure_loudness, normalize_loudness, adjust_color, finish_film,
        DEFAULT_TARGET_LUFS,
        validate_loudness_report_schema, validate_color_adjustment_schema,
        validate_finishing_result_schema,
        generate_finishing_result_id, is_valid_finishing_result_id,
        FinishingError,
    )
"""
from __future__ import annotations

from .builder import DEFAULT_TARGET_LUFS, finish_film
from .errors import FinishingError
from .ids import generate_finishing_result_id, is_valid_finishing_result_id
from .models import ColorAdjustment, FinishingResult, LoudnessReport
from .pipeline import adjust_color, measure_loudness, normalize_loudness
from .schema import (
    validate_color_adjustment_schema, validate_finishing_result_schema, validate_loudness_report_schema,
)

__all__ = [
    "DEFAULT_TARGET_LUFS", "ColorAdjustment", "FinishingError", "FinishingResult", "LoudnessReport",
    "adjust_color", "finish_film", "generate_finishing_result_id", "is_valid_finishing_result_id",
    "measure_loudness", "normalize_loudness", "validate_color_adjustment_schema",
    "validate_finishing_result_schema", "validate_loudness_report_schema",
]
