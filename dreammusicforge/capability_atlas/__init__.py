"""DreamMusicForge Film Compiler -- capability_atlas package (Release 0.5).

Public API:

    from dreammusicforge.capability_atlas import (
        CAPABILITY_STATUSES, RendererCapability, RendererCapabilityProfile,
        ShotFitScore, ProviderFitReport,
        build_capability, build_capability_profile,
        validate_capability_schema, validate_capability_profile_schema,
        score_capability_status, evaluate_shot_fit, rank_providers_for_shot,
        CapabilityAtlasValidationError,
    )

Everything else in the full spec (Video Slicer, provider compilers,
verification, repair, assembly, ...) is later releases and is not
present here.
"""
from __future__ import annotations

from .builder import build_capability, build_capability_profile
from .errors import CapabilityAtlasValidationError
from .models import (
    CAPABILITY_STATUSES, ProviderFitReport, RendererCapability, RendererCapabilityProfile, ShotFitScore,
)
from .schema import validate_capability_profile_schema, validate_capability_schema
from .scoring import evaluate_shot_fit, rank_providers_for_shot, score_capability_status

__all__ = [
    "CAPABILITY_STATUSES", "CapabilityAtlasValidationError", "ProviderFitReport", "RendererCapability",
    "RendererCapabilityProfile", "ShotFitScore", "build_capability", "build_capability_profile",
    "evaluate_shot_fit", "rank_providers_for_shot", "score_capability_status",
    "validate_capability_profile_schema", "validate_capability_schema",
]
