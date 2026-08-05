"""Strategy selection: turns a shot's ProviderFitReport (Release 0.5)
into one of spec section 7.4's five named strategies -- this release's
"strategy selection" deliverable (spec section 19).

Four of the five strategies are selected by a deterministic decision
procedure built only from signals this repository's models actually
carry. `editorial_illusion` is never auto-selected: section 7.4's own
"Select when" bullets for it ("intended meaning can be preserved through
inserts," "cutaways can conceal defects," "symbolic imagery can replace
literal complexity") are creative and symbolic judgments -- there is no
field anywhere in this repository's domain model that represents "can
this defect be concealed by a cutaway," and fabricating a proxy for it
would be exactly the kind of placeholder logic spec section 22 forbids
labeling complete. A future release with an actual creative-review
input could add it; this one can't claim it.

The decision procedure, in order:

1. If any provider is unconditionally qualified for the whole shot
   (Release 0.5's evaluate_shot_fit didn't disqualify it), pick the
   top-ranked one and choose between:
   - `direct_render`: simple shots (<=2 characters, low choreography
     risk, no continuity dependency, solid fit score) -- section 7.4's
     Direct Render bullets, mapped onto RiskFactors.
   - `layered_compositing`: everything else that's still qualified --
     more characters, higher choreography risk, or a weaker fit score
     all point at decomposing the shot into safer layers rather than
     trusting one direct pass.
2. If nothing is unconditionally qualified, look for a provider that was
   disqualified *only* for exceeding the shot's duration and that
   declares positive-evidence support for a continuation-style
   capability (`video_extension` or `last_frame_seed`, matching this
   same repository's pre-spec `runtime.py` continuity-mode vocabulary):
   `controlled_continuation`.
3. Otherwise: `external_production_required`, with a FallbackPlan
   quoting section 7.4's own recommendation ("a conventional or
   dedicated specialist tool is more reliable").
"""
from __future__ import annotations

from ..capability_atlas.models import ProviderFitReport, RendererCapabilityProfile
from ..production.models import Shot
from .models import StrategyDecision
from .risk import compute_risk_factors

DIRECT_RENDER_MAX_CHARACTERS = 2
DIRECT_RENDER_MAX_CHOREOGRAPHY_RISK = 30.0
DIRECT_RENDER_MIN_FIT_SCORE = 70.0
DIRECT_RENDER_MAX_CONTINUITY_DEPENDENCY_RISK = 30.0

_CONTINUATION_CAPABILITY_NAMES = frozenset({"video_extension", "last_frame_seed"})
_POSITIVE_EVIDENCE_STATUSES = frozenset({"verified", "measured", "assumed"})


def _has_continuation_support(profile: RendererCapabilityProfile) -> bool:
    return any(
        capability.name in _CONTINUATION_CAPABILITY_NAMES and capability.status in _POSITIVE_EVIDENCE_STATUSES
        for capability in profile.capabilities
    )


def select_strategy(
    shot: Shot,
    fit_report: ProviderFitReport,
    profiles_by_provider: dict[str, RendererCapabilityProfile],
    has_predecessor: bool = False,
) -> StrategyDecision:
    qualified = [score for score in fit_report.scores if not score.disqualified]

    if qualified:
        best = qualified[0]
        profile = profiles_by_provider[best.provider]
        risk = compute_risk_factors(shot, profile, best, has_predecessor)

        if (
            shot.requirements.character_count <= DIRECT_RENDER_MAX_CHARACTERS
            and risk.choreography_complexity <= DIRECT_RENDER_MAX_CHOREOGRAPHY_RISK
            and risk.continuity_dependency <= DIRECT_RENDER_MAX_CONTINUITY_DEPENDENCY_RISK
            and best.overall_score >= DIRECT_RENDER_MIN_FIT_SCORE
        ):
            return StrategyDecision(
                strategy="direct_render", provider=best.provider, risk_factors=risk,
                reasons=(
                    f"{best.provider} is qualified with fit score {best.overall_score}",
                    f"character_count {shot.requirements.character_count} <= {DIRECT_RENDER_MAX_CHARACTERS}",
                    f"choreography risk {risk.choreography_complexity} <= {DIRECT_RENDER_MAX_CHOREOGRAPHY_RISK}",
                ),
            )

        return StrategyDecision(
            strategy="layered_compositing", provider=best.provider, risk_factors=risk,
            reasons=(
                f"{best.provider} is qualified with fit score {best.overall_score}",
                "shot does not meet direct_render's low-complexity thresholds",
            ),
        )

    for score in fit_report.scores:
        duration_only = bool(score.disqualification_reasons) and all(
            "duration" in reason for reason in score.disqualification_reasons
        )
        if not duration_only:
            continue
        profile = profiles_by_provider[score.provider]
        if _has_continuation_support(profile):
            risk = compute_risk_factors(shot, profile, score, has_predecessor)
            return StrategyDecision(
                strategy="controlled_continuation", provider=score.provider, risk_factors=risk,
                reasons=(
                    f"{score.provider} was disqualified only for exceeding max_duration_seconds",
                    f"{score.provider} declares continuation support ({sorted(_CONTINUATION_CAPABILITY_NAMES)})",
                ),
            )

    return StrategyDecision(
        strategy="external_production_required", provider=None, risk_factors=None,
        reasons=(
            "no provider is qualified for this shot",
            "no disqualified-for-duration-only provider declares continuation support",
        ),
    )
