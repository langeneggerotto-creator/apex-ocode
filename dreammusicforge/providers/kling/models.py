from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from dreammusicforge.production_strategy.models import ProductionRisk, ProductionStrategy


class KlingMode(str, Enum):
    TEXT_TO_VIDEO = "TEXT_TO_VIDEO"
    IMAGE_TO_VIDEO = "IMAGE_TO_VIDEO"
    START_FRAME_CONTINUATION = "START_FRAME_CONTINUATION"
    MOTION_CONTROL = "MOTION_CONTROL"
    MULTI_SHOT = "MULTI_SHOT"
    LAYERED_PASS = "LAYERED_PASS"
    EXTERNAL_STAGE = "EXTERNAL_STAGE"
    REDESIGN = "REDESIGN"


@dataclass(frozen=True)
class KlingReference:
    reference_id: str
    reference_type: str
    required: bool = True
    purpose: str = ""

    def validate(self) -> None:
        if not self.reference_id.strip():
            raise ValueError("reference_id is required")
        if not self.reference_type.strip():
            raise ValueError("reference_type is required")


@dataclass(frozen=True)
class KlingExecutionPackage:
    package_id: str
    transition_id: str
    strategy: ProductionStrategy
    risk: ProductionRisk
    mode: KlingMode
    duration_seconds: float
    prompt: str
    negative_constraints: tuple[str, ...]
    references: tuple[KlingReference, ...]
    candidate_count: int
    acceptance_gates: tuple[str, ...]
    fallback_plan: tuple[str, ...]
    requires_external_master_audio: bool = True
    requires_external_lip_sync: bool = False

    def validate(self) -> None:
        if not self.package_id.strip():
            raise ValueError("package_id is required")
        if not self.transition_id.strip():
            raise ValueError("transition_id is required")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        if not self.prompt.strip() and self.mode not in {KlingMode.EXTERNAL_STAGE, KlingMode.REDESIGN}:
            raise ValueError("prompt is required for executable Kling modes")
        if self.candidate_count < 1:
            raise ValueError("candidate_count must be >= 1")
        for reference in self.references:
            reference.validate()
