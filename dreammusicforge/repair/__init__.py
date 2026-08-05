"""DreamMusicForge Film Compiler -- repair package (Release 0.10).

Public API:

    from dreammusicforge.repair import (
        REPAIR_ACTIONS, SEVERITY_LEVELS, DECISION_VALUES,
        Defect, RepairPlan, VerificationResult,
        score_technical_report,
        DEFAULT_CRITICAL_THRESHOLDS, METRIC_RECOMMENDATIONS, classify_failures,
        build_repair_plan, evaluate_candidate,
        validate_defect_schema, validate_repair_plan_schema, validate_verification_result_schema,
        generate_defect_id, is_valid_defect_id,
        AcceptanceRepairError,
    )

Everything else in the full spec (assembly, lip-sync, compositing,
color/audio finishing, ...) is later releases and is not present here.
"""
from __future__ import annotations

from .builder import build_repair_plan, evaluate_candidate
from .classifier import DEFAULT_CRITICAL_THRESHOLDS, METRIC_RECOMMENDATIONS, classify_failures
from .errors import AcceptanceRepairError
from .ids import generate_defect_id, is_valid_defect_id
from .models import DECISION_VALUES, REPAIR_ACTIONS, SEVERITY_LEVELS, Defect, RepairPlan, VerificationResult
from .schema import validate_defect_schema, validate_repair_plan_schema, validate_verification_result_schema
from .scoring import score_technical_report

__all__ = [
    "AcceptanceRepairError", "DECISION_VALUES", "DEFAULT_CRITICAL_THRESHOLDS", "Defect",
    "METRIC_RECOMMENDATIONS", "REPAIR_ACTIONS", "RepairPlan", "SEVERITY_LEVELS", "VerificationResult",
    "build_repair_plan", "classify_failures", "evaluate_candidate", "generate_defect_id",
    "is_valid_defect_id", "score_technical_report", "validate_defect_schema", "validate_repair_plan_schema",
    "validate_verification_result_schema",
]
