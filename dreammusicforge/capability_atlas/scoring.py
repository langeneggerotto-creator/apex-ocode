"""Capability scoring: a pure, deterministic function from a
RendererCapability's Law-3.10 status to a numeric score, plus the
shot-fit evaluation and renderer ranking built on top of it -- this
release's other three "Build" deliverables (spec section 19).

The exact numbers (100 / 80 / 55 / 0 / 0) are this release's own
interpretation, not spec-mandated -- the spec requires the five-way
distinction (Law 3.10) but gives no scoring formula. They're chosen to
be strictly decreasing in the order Law 3.10 lists the five statuses,
and `unsupported` and `unknown` deliberately score identically (zero):
a provider-fit report should never reward the *absence* of positive
evidence over a *confirmed* lack of support -- Law 3.7's "fail closed"
read onto ranking. The stored `status` field never collapses the two,
though; only their score contribution does.
"""
from __future__ import annotations

from ..production.models import Shot
from .models import ProviderFitReport, RendererCapabilityProfile, ShotFitScore

CAPABILITY_STATUS_SCORES: dict[str, float] = {
    "verified": 100.0,
    "measured": 80.0,
    "assumed": 55.0,
    "unsupported": 0.0,
    "unknown": 0.0,
}

_POSITIVE_EVIDENCE_STATUSES = frozenset({"verified", "measured", "assumed"})


def score_capability_status(status: str) -> float:
    return CAPABILITY_STATUS_SCORES[status]


def evaluate_shot_fit(shot: Shot, profile: RendererCapabilityProfile) -> ShotFitScore:
    """Hard requirements (duration, character count, camera motion,
    lip sync) disqualify a provider outright -- a disqualified provider
    gets overall_score 0.0 and empty capability_scores, since a fit
    score for a shot a provider structurally cannot render would be
    meaningless. Providers that pass are scored on every capability
    named in the shot's own acceptance thresholds (spec section 6.8):
    a capability the profile doesn't declare at all scores 0.0 for that
    dimension -- no declaration is no evidence, same fail-closed logic
    as the status-score mapping above."""
    reasons: list[str] = []
    duration = shot.timing.end_seconds - shot.timing.start_seconds

    if duration > profile.max_duration_seconds:
        reasons.append(f"shot duration {duration}s exceeds provider max_duration_seconds {profile.max_duration_seconds}s")
    if shot.requirements.character_count > profile.max_character_count:
        reasons.append(f"shot character_count {shot.requirements.character_count} exceeds provider max_character_count {profile.max_character_count}")
    if shot.requirements.camera_motion not in profile.supported_camera_motions:
        reasons.append(f"shot camera_motion {shot.requirements.camera_motion!r} is not in provider supported_camera_motions {list(profile.supported_camera_motions)}")

    capabilities_by_name = {capability.name: capability for capability in profile.capabilities}

    if shot.requirements.lip_sync_required:
        lip_sync = capabilities_by_name.get("lip_sync")
        if lip_sync is None or lip_sync.status not in _POSITIVE_EVIDENCE_STATUSES:
            status = lip_sync.status if lip_sync is not None else "undeclared"
            reasons.append(f"shot requires lip_sync but provider capability status is {status!r}, not one of {sorted(_POSITIVE_EVIDENCE_STATUSES)}")

    if reasons:
        return ShotFitScore(
            provider=profile.provider, shot_id=shot.id, disqualified=True,
            disqualification_reasons=tuple(reasons), capability_scores={}, overall_score=0.0,
        )

    capability_scores = {
        name: score_capability_status(capabilities_by_name[name].status) if name in capabilities_by_name else 0.0
        for name in shot.acceptance
    }
    overall_score = sum(capability_scores.values()) / len(capability_scores) if capability_scores else 0.0

    return ShotFitScore(
        provider=profile.provider, shot_id=shot.id, disqualified=False,
        disqualification_reasons=(), capability_scores=capability_scores, overall_score=overall_score,
    )


def rank_providers_for_shot(shot: Shot, profiles: tuple[RendererCapabilityProfile, ...]) -> ProviderFitReport:
    """The "renderer ranking" deliverable: every profile is scored, then
    ordered qualified-first (by descending overall_score, ties broken by
    provider name for determinism), disqualified providers last (also by
    provider name). recommended_provider is the top qualified provider,
    or None if every profile was disqualified."""
    scores = tuple(evaluate_shot_fit(shot, profile) for profile in profiles)
    ordered = tuple(sorted(scores, key=lambda score: (score.disqualified, -score.overall_score, score.provider)))
    recommended = ordered[0].provider if ordered and not ordered[0].disqualified else None
    return ProviderFitReport(shot_id=shot.id, scores=ordered, recommended_provider=recommended)
