from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProductionStrategy(str, Enum):
    DIRECT_RENDER = "DIRECT_RENDER"
    CONTROLLED_CONTINUATION = "CONTROLLED_CONTINUATION"
    LAYERED_COMPOSITING = "LAYERED_COMPOSITING"
    EDITORIAL_ILLUSION = "EDITORIAL_ILLUSION"
    EXTERNAL_SPECIALIST_STAGE = "EXTERNAL_SPECIALIST_STAGE"
    REDESIGN_REQUIRED = "REDESIGN_REQUIRED"


class ProductionRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


@dataclass(frozen=True)
class CapabilityProfile:
    renderer_id: str
    max_duration_seconds: float
    supports_start_frame: bool
    supports_end_frame: bool
    supports_motion_control: bool
    supports_character_reference: bool
    supports_multi_character: bool
    supports_native_audio: bool
    supports_lip_sync: bool
    max_reliable_characters: int = 1

    def validate(self) -> None:
        if not self.renderer_id.strip():
            raise ValueError("renderer_id is required")
        if self.max_duration_seconds <= 0:
            raise ValueError("max_duration_seconds must be positive")
        if self.max_reliable_characters < 1:
            raise ValueError("max_reliable_characters must be >= 1")


@dataclass(frozen=True)
class TransitionRequirements:
    transition_id: str
    duration_seconds: float
    character_count: int = 1
    exact_identity_required: bool = True
    exact_costume_required: bool = True
    exact_world_required: bool = True
    lip_sync_required: bool = False
    choreography_complexity: int = 0
    camera_complexity: int = 0
    hand_object_interaction: bool = False
    continuous_take_required: bool = False
    can_use_cutaways: bool = True
    can_layer_subjects: bool = True
    external_specialist_available: bool = True

    def validate(self) -> None:
        if not self.transition_id.strip():
            raise ValueError("transition_id is required")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        if self.character_count < 1:
            raise ValueError("character_count must be >= 1")
        for name, value in (
            ("choreography_complexity", self.choreography_complexity),
            ("camera_complexity", self.camera_complexity),
        ):
            if not 0 <= value <= 3:
                raise ValueError(f"{name} must be between 0 and 3")


@dataclass(frozen=True)
class StrategyDecision:
    transition_id: str
    strategy: ProductionStrategy
    risk: ProductionRisk
    reasons: tuple[str, ...]
    mitigations: tuple[str, ...]
