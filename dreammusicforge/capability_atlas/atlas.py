from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

RISK_BANDS = (
    (90, "LOW"),
    (75, "MODERATE"),
    (60, "HIGH"),
    (0, "VERY_HIGH"),
)

CRITICAL_DIMENSIONS = {
    "identity",
    "hair",
    "wardrobe",
    "stage",
    "audio_continuity",
    "lip_sync",
}


@dataclass(frozen=True)
class ShotRequirement:
    shot_id: str
    duration_seconds: float
    required_capabilities: Dict[str, float]
    complexity_factors: Dict[str, float]


@dataclass(frozen=True)
class RendererRecommendation:
    renderer_id: str
    fit_score: float
    risk_band: str
    accepted: bool
    failures: List[str]
    mitigations: List[str]


def _risk_band(score: float) -> str:
    for minimum, label in RISK_BANDS:
        if score >= minimum:
            return label
    return "VERY_HIGH"


def validate_profile(profile: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not profile.get("renderer_id"):
        errors.append("renderer_id is required")
    capabilities = profile.get("capabilities")
    if not isinstance(capabilities, dict) or not capabilities:
        errors.append("capabilities must be a non-empty mapping")
    else:
        for name, entry in capabilities.items():
            if not isinstance(entry, dict):
                errors.append(f"capability {name} must be an object")
                continue
            value = entry.get("score")
            if not isinstance(value, (int, float)) or not 0 <= value <= 100:
                errors.append(f"capability {name} score must be between 0 and 100")
            if entry.get("evidence_status") not in {
                "MEASURED",
                "ASSUMED_UNTIL_BENCHMARKED",
                "UNKNOWN",
            }:
                errors.append(f"capability {name} has invalid evidence_status")
    max_duration = profile.get("max_duration_seconds")
    if not isinstance(max_duration, (int, float)) or max_duration <= 0:
        errors.append("max_duration_seconds must be positive")
    return errors


def evaluate_renderer(
    profile: Dict[str, Any],
    shot: ShotRequirement,
) -> RendererRecommendation:
    errors = validate_profile(profile)
    if errors:
        raise ValueError("Invalid renderer profile: " + "; ".join(errors))

    failures: List[str] = []
    mitigations: List[str] = []
    scores: List[float] = []

    if shot.duration_seconds > float(profile["max_duration_seconds"]):
        failures.append(
            f"duration {shot.duration_seconds:.1f}s exceeds renderer limit "
            f"{profile['max_duration_seconds']:.1f}s"
        )
        mitigations.append("split the shot or use verified continuation mode")

    capabilities = profile["capabilities"]
    for capability, required in shot.required_capabilities.items():
        entry = capabilities.get(capability)
        if entry is None:
            failures.append(f"missing capability evidence: {capability}")
            mitigations.append(f"benchmark {capability} before production")
            scores.append(0.0)
            continue
        actual = float(entry["score"])
        scores.append(min(100.0, actual / max(required, 1.0) * 100.0))
        if actual < required:
            failures.append(
                f"{capability} {actual:.1f} is below required {required:.1f}"
            )
            if capability in CRITICAL_DIMENSIONS:
                mitigations.append(
                    f"lock {capability} with references and reject failed renders"
                )
            else:
                mitigations.append(f"simplify or externally control {capability}")

    complexity_penalty = sum(max(0.0, value) for value in shot.complexity_factors.values())
    raw_score = sum(scores) / len(scores) if scores else 0.0
    fit_score = max(0.0, min(100.0, raw_score - complexity_penalty))

    critical_failure = any(
        failure.split(" ", 1)[0] in CRITICAL_DIMENSIONS for failure in failures
    )
    accepted = not failures and not critical_failure and fit_score >= 80.0

    return RendererRecommendation(
        renderer_id=profile["renderer_id"],
        fit_score=round(fit_score, 2),
        risk_band=_risk_band(fit_score),
        accepted=accepted,
        failures=failures,
        mitigations=sorted(set(mitigations)),
    )


def rank_renderers(
    profiles: Iterable[Dict[str, Any]],
    shot: ShotRequirement,
) -> List[RendererRecommendation]:
    results = [evaluate_renderer(profile, shot) for profile in profiles]
    return sorted(results, key=lambda item: item.fit_score, reverse=True)
