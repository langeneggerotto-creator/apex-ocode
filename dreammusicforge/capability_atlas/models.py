"""Typed domain model for Release 0.5 -- "shot requirements produce a
provider-fit report" (spec section 19's acceptance test for this
release).

CAPABILITY_STATUSES matches spec Law 3.10 verbatim: "The system must
distinguish: verified capability; measured capability; assumed
capability; unsupported capability; unknown capability." Everything else
here (the exact fields on RendererCapabilityProfile, the scoring
numbers) is this release's own design -- the spec names
`capability_atlas/profiles/` in its architecture diagram (section 5) and
"provider profiles" in section 19's Build list, but gives no worked YAML
example the way sections 6.1-6.11 do for other entities. See
`capability_atlas/scoring.py`'s module docstring for the scoring
rationale.

Same to_dict()/from_dict() convention as the rest of this repo's
domain models -- frozen dataclasses, not the JSON-Schema-in-a-dict
pattern used elsewhere in this repo's sibling dreammusicforge module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CAPABILITY_STATUSES = ("verified", "measured", "assumed", "unsupported", "unknown")


@dataclass(frozen=True)
class RendererCapability:
    name: str
    status: str
    evidence: str | None = None

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "evidence": self.evidence}

    @staticmethod
    def from_dict(data: dict) -> "RendererCapability":
        return RendererCapability(name=data["name"], status=data["status"], evidence=data.get("evidence"))


@dataclass(frozen=True)
class RendererCapabilityProfile:
    provider: str
    max_duration_seconds: float
    max_character_count: int
    supported_camera_motions: tuple[str, ...]
    capabilities: tuple[RendererCapability, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "max_duration_seconds": self.max_duration_seconds,
            "max_character_count": self.max_character_count,
            "supported_camera_motions": list(self.supported_camera_motions),
            "capabilities": [capability.to_dict() for capability in self.capabilities],
        }

    @staticmethod
    def from_dict(data: dict) -> "RendererCapabilityProfile":
        return RendererCapabilityProfile(
            provider=data["provider"],
            max_duration_seconds=float(data["max_duration_seconds"]),
            max_character_count=int(data["max_character_count"]),
            supported_camera_motions=tuple(data.get("supported_camera_motions", [])),
            capabilities=tuple(RendererCapability.from_dict(item) for item in data.get("capabilities", [])),
        )


@dataclass(frozen=True)
class ShotFitScore:
    provider: str
    shot_id: str
    disqualified: bool
    disqualification_reasons: tuple[str, ...]
    capability_scores: dict[str, float]
    overall_score: float

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "shot_id": self.shot_id,
            "disqualified": self.disqualified,
            "disqualification_reasons": list(self.disqualification_reasons),
            "capability_scores": dict(self.capability_scores),
            "overall_score": self.overall_score,
        }

    @staticmethod
    def from_dict(data: dict) -> "ShotFitScore":
        return ShotFitScore(
            provider=data["provider"],
            shot_id=data["shot_id"],
            disqualified=bool(data["disqualified"]),
            disqualification_reasons=tuple(data.get("disqualification_reasons", [])),
            capability_scores=dict(data.get("capability_scores", {})),
            overall_score=float(data["overall_score"]),
        )


@dataclass(frozen=True)
class ProviderFitReport:
    shot_id: str
    scores: tuple[ShotFitScore, ...]
    recommended_provider: str | None

    def to_dict(self) -> dict:
        return {
            "shot_id": self.shot_id,
            "scores": [score.to_dict() for score in self.scores],
            "recommended_provider": self.recommended_provider,
        }

    @staticmethod
    def from_dict(data: dict) -> "ProviderFitReport":
        return ProviderFitReport(
            shot_id=data["shot_id"],
            scores=tuple(ShotFitScore.from_dict(item) for item in data.get("scores", [])),
            recommended_provider=data.get("recommended_provider"),
        )
