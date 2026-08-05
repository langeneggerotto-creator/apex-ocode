"""Typed domain model for Release 0.6 -- "complex shot becomes
executable render tasks" (spec section 19's acceptance test for this
release).

RISK_FACTOR_NAMES matches spec section 7.3's `risk_factors` list
verbatim: duration, character_count, identity_precision,
costume_precision, world_precision, prop_interaction,
choreography_complexity, camera_motion, lip_sync, facial_performance,
hand_complexity, lighting_change, transition_complexity,
continuity_dependency, provider_support. Ten of those are computed by
`slicer/risk.py`'s `compute_risk_factors()` from data this repository's
domain models actually carry (Shot, RendererCapabilityProfile,
ShotFitScore); five (`prop_interaction`, `facial_performance`,
`hand_complexity`, `lighting_change`, `transition_complexity`) stay
`None` -- nothing in this release's Shot model captures props, facial
expression, hand poses, lighting design, or transition type, and
spec section 7.3's own YAML template shows every factor as an empty
placeholder with no worked example to derive a formula from. Fabricating
a number for those five would violate the spec's own rule (section 22)
against placeholder logic labeled complete; leaving them `None` states
the gap instead of hiding it.

SLICING_STRATEGIES matches spec section 7.4's five named strategies.
`slicer/strategy.py`'s `select_strategy()` computes four of them
deterministically; `editorial_illusion` is never auto-selected -- see
that module's docstring for why.

Same to_dict()/from_dict() convention as the rest of this repo's domain
models -- frozen dataclasses, not the JSON-Schema-in-a-dict pattern used
elsewhere in this repo's sibling dreammusicforge module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

RISK_FACTOR_NAMES = (
    "duration", "character_count", "identity_precision", "costume_precision", "world_precision",
    "prop_interaction", "choreography_complexity", "camera_motion", "lip_sync", "facial_performance",
    "hand_complexity", "lighting_change", "transition_complexity", "continuity_dependency", "provider_support",
)

UNASSESSED_RISK_FACTOR_NAMES = (
    "prop_interaction", "facial_performance", "hand_complexity", "lighting_change", "transition_complexity",
)

SLICING_STRATEGIES = (
    "direct_render", "controlled_continuation", "layered_compositing", "editorial_illusion",
    "external_production_required",
)

EXPECTED_RENDER_OUTPUTS = ("candidate_video", "final_frame")


@dataclass(frozen=True)
class RiskFactors:
    duration: float
    character_count: float
    identity_precision: float
    costume_precision: float
    world_precision: float
    choreography_complexity: float
    camera_motion: float
    lip_sync: float
    continuity_dependency: float
    provider_support: float
    prop_interaction: float | None = None
    facial_performance: float | None = None
    hand_complexity: float | None = None
    lighting_change: float | None = None
    transition_complexity: float | None = None

    def to_dict(self) -> dict:
        return {name: getattr(self, name) for name in RISK_FACTOR_NAMES}

    @staticmethod
    def from_dict(data: dict) -> "RiskFactors":
        kwargs = {name: data[name] for name in RISK_FACTOR_NAMES if name not in UNASSESSED_RISK_FACTOR_NAMES}
        kwargs.update({name: data.get(name) for name in UNASSESSED_RISK_FACTOR_NAMES})
        return RiskFactors(**kwargs)


@dataclass(frozen=True)
class TemporalSlice:
    id: str
    index: int
    start_seconds: float
    end_seconds: float

    def to_dict(self) -> dict:
        return {"id": self.id, "index": self.index, "start_seconds": self.start_seconds, "end_seconds": self.end_seconds}

    @staticmethod
    def from_dict(data: dict) -> "TemporalSlice":
        return TemporalSlice(
            id=data["id"], index=int(data["index"]),
            start_seconds=float(data["start_seconds"]), end_seconds=float(data["end_seconds"]),
        )


@dataclass(frozen=True)
class VisualLayer:
    id: str
    name: str

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}

    @staticmethod
    def from_dict(data: dict) -> "VisualLayer":
        return VisualLayer(id=data["id"], name=data["name"])


@dataclass(frozen=True)
class MotionLayer:
    id: str
    name: str
    camera_motion: str

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "camera_motion": self.camera_motion}

    @staticmethod
    def from_dict(data: dict) -> "MotionLayer":
        return MotionLayer(id=data["id"], name=data["name"], camera_motion=data["camera_motion"])


@dataclass(frozen=True)
class StrategyDecision:
    strategy: str
    provider: str | None
    risk_factors: RiskFactors | None
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "provider": self.provider,
            "risk_factors": self.risk_factors.to_dict() if self.risk_factors is not None else None,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class FallbackPlan:
    reason: str
    recommended_action: str

    def to_dict(self) -> dict:
        return {"reason": self.reason, "recommended_action": self.recommended_action}

    @staticmethod
    def from_dict(data: dict) -> "FallbackPlan":
        return FallbackPlan(reason=data["reason"], recommended_action=data["recommended_action"])


@dataclass(frozen=True)
class RenderTask:
    id: str
    shot_id: str
    slice_id: str
    provider: str
    duration_seconds: float
    required_assets: tuple[str, ...]
    expected_outputs: tuple[str, ...] = EXPECTED_RENDER_OUTPUTS
    critical_checks: tuple[str, ...] = field(default_factory=tuple)
    mode: str | None = None
    prompt_file: str | None = None
    negative_prompt_file: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "shot_id": self.shot_id,
            "slice_id": self.slice_id,
            "provider": self.provider,
            "duration_seconds": self.duration_seconds,
            "required_assets": list(self.required_assets),
            "expected_outputs": list(self.expected_outputs),
            "critical_checks": list(self.critical_checks),
            "mode": self.mode,
            "prompt_file": self.prompt_file,
            "negative_prompt_file": self.negative_prompt_file,
        }

    @staticmethod
    def from_dict(data: dict) -> "RenderTask":
        return RenderTask(
            id=data["id"],
            shot_id=data["shot_id"],
            slice_id=data["slice_id"],
            provider=data["provider"],
            duration_seconds=float(data["duration_seconds"]),
            required_assets=tuple(data.get("required_assets", [])),
            expected_outputs=tuple(data.get("expected_outputs", EXPECTED_RENDER_OUTPUTS)),
            critical_checks=tuple(data.get("critical_checks", [])),
            mode=data.get("mode"),
            prompt_file=data.get("prompt_file"),
            negative_prompt_file=data.get("negative_prompt_file"),
        )


@dataclass(frozen=True)
class SliceResult:
    shot_id: str
    strategy: str
    provider: str | None
    reasons: tuple[str, ...]
    risk_factors: RiskFactors | None
    temporal_slices: tuple[TemporalSlice, ...]
    visual_layers: tuple[VisualLayer, ...]
    motion_layers: tuple[MotionLayer, ...]
    render_tasks: tuple[RenderTask, ...]
    fallback_plan: FallbackPlan | None

    def to_dict(self) -> dict:
        return {
            "shot_id": self.shot_id,
            "strategy": self.strategy,
            "provider": self.provider,
            "reasons": list(self.reasons),
            "risk_factors": self.risk_factors.to_dict() if self.risk_factors is not None else None,
            "temporal_slices": [item.to_dict() for item in self.temporal_slices],
            "visual_layers": [item.to_dict() for item in self.visual_layers],
            "motion_layers": [item.to_dict() for item in self.motion_layers],
            "render_tasks": [item.to_dict() for item in self.render_tasks],
            "fallback_plan": self.fallback_plan.to_dict() if self.fallback_plan is not None else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "SliceResult":
        risk_data = data.get("risk_factors")
        fallback_data = data.get("fallback_plan")
        return SliceResult(
            shot_id=data["shot_id"],
            strategy=data["strategy"],
            provider=data.get("provider"),
            reasons=tuple(data.get("reasons", [])),
            risk_factors=RiskFactors.from_dict(risk_data) if risk_data is not None else None,
            temporal_slices=tuple(TemporalSlice.from_dict(item) for item in data.get("temporal_slices", [])),
            visual_layers=tuple(VisualLayer.from_dict(item) for item in data.get("visual_layers", [])),
            motion_layers=tuple(MotionLayer.from_dict(item) for item in data.get("motion_layers", [])),
            render_tasks=tuple(RenderTask.from_dict(item) for item in data.get("render_tasks", [])),
            fallback_plan=FallbackPlan.from_dict(fallback_data) if fallback_data is not None else None,
        )
