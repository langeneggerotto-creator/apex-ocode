"""Risk analysis: deterministic risk-factor computation from a Shot, the
RendererCapabilityProfile it was scored against, and the ShotFitScore
Release 0.5 already produced for that pairing -- this release's "risk
analysis" deliverable (spec section 19).

Every number here is grounded in a field this repository's domain model
actually carries. Where the spec names a risk factor this release has no
signal for (see models.py's RISK_FACTOR_NAMES docstring), it's left
`None` rather than fabricated.
"""
from __future__ import annotations

from ..capability_atlas.models import RendererCapabilityProfile, ShotFitScore
from ..production.models import Shot
from .models import RiskFactors

CHOREOGRAPHY_COMPLEXITY_RISK: dict[str, float] = {"low": 20.0, "medium": 50.0, "high": 80.0}
DEFAULT_CHOREOGRAPHY_COMPLEXITY_RISK = 50.0

CONTINUITY_DEPENDENCY_WITH_PREDECESSOR = 70.0
CONTINUITY_DEPENDENCY_WITHOUT_PREDECESSOR = 20.0


def compute_risk_factors(
    shot: Shot,
    profile: RendererCapabilityProfile,
    fit_score: ShotFitScore,
    has_predecessor: bool = False,
) -> RiskFactors:
    """`fit_score` must be the result of evaluating `shot` against
    `profile` (i.e. `evaluate_shot_fit(shot, profile)`); this function
    doesn't re-run that evaluation, it reads risk signal out of it.
    `has_predecessor` should be True when `shot` chains continuity from
    an earlier shot in the same sequence and performer (see
    production/schema.py's state-chaining check) -- a chained shot
    carries more continuity risk than a standalone one, since a defect
    upstream cascades."""
    duration_seconds = shot.timing.end_seconds - shot.timing.start_seconds
    duration = min(100.0, (duration_seconds / profile.max_duration_seconds) * 100.0)
    character_count = min(100.0, (shot.requirements.character_count / profile.max_character_count) * 100.0)

    choreography_complexity = CHOREOGRAPHY_COMPLEXITY_RISK.get(
        shot.requirements.choreography_complexity.strip().lower(), DEFAULT_CHOREOGRAPHY_COMPLEXITY_RISK,
    )
    camera_motion = 0.0 if shot.requirements.camera_motion in profile.supported_camera_motions else 100.0
    lip_sync = (100.0 - fit_score.capability_scores.get("lip_sync", 0.0)) if shot.requirements.lip_sync_required else 0.0

    identity_precision = 100.0 - fit_score.capability_scores.get("identity", 0.0)
    costume_precision = 100.0 - fit_score.capability_scores.get("costume", 0.0)
    world_precision = 100.0 - fit_score.capability_scores.get("world", 0.0)

    continuity_dependency = CONTINUITY_DEPENDENCY_WITH_PREDECESSOR if has_predecessor else CONTINUITY_DEPENDENCY_WITHOUT_PREDECESSOR
    provider_support = 100.0 if fit_score.disqualified else (100.0 - fit_score.overall_score)

    return RiskFactors(
        duration=duration,
        character_count=character_count,
        identity_precision=identity_precision,
        costume_precision=costume_precision,
        world_precision=world_precision,
        choreography_complexity=choreography_complexity,
        camera_motion=camera_motion,
        lip_sync=lip_sync,
        continuity_dependency=continuity_dependency,
        provider_support=provider_support,
    )
