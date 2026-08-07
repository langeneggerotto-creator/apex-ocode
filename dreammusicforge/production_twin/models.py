from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Mapping


@dataclass(frozen=True)
class PerformerState:
    performer_id: str
    identity_id: str
    costume_id: str
    hair_id: str
    makeup_id: str | None = None
    pose: str = "neutral"
    gaze: str = "unspecified"
    action: str = "hold"
    emotional_state: str = "neutral"


@dataclass(frozen=True)
class CameraState:
    shot_size: str
    lens_mm: float | None
    height: str
    movement: str
    axis: str


@dataclass(frozen=True)
class LightingState:
    lighting_id: str
    key: str
    fill: str
    rim: str
    atmosphere: str
    palette_id: str


@dataclass(frozen=True)
class MusicState:
    song_id: str
    time_seconds: float
    section_id: str
    beat_id: str | None = None
    lyric_id: str | None = None
    energy: float = 0.0


@dataclass(frozen=True)
class ExperienceState:
    experience_id: str
    primary_emotion: str
    intensity: float
    intended_inference: str


@dataclass(frozen=True)
class WorldState:
    world_id: str
    geometry_state_id: str
    prop_state_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TwinState:
    state_id: str
    start_seconds: float
    end_seconds: float
    performer: PerformerState
    camera: CameraState
    lighting: LightingState
    music: MusicState
    experience: ExperienceState
    world: WorldState
    invariants: tuple[str, ...] = ()
    allowed_mutations: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TwinTransition:
    transition_id: str
    source_state_id: str
    destination_state_id: str
    declared_changes: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class ProductionTwin:
    twin_id: str
    project_id: str
    states: tuple[TwinState, ...]
    transitions: tuple[TwinTransition, ...]
    duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RendererTaskContract:
    task_id: str
    source_state_id: str
    destination_state_id: str
    duration_seconds: float
    required_invariants: tuple[str, ...]
    permitted_changes: tuple[str, ...]
    performer_id: str
    costume_id: str
    hair_id: str
    world_id: str
    camera: CameraState
    lighting: LightingState
    music_start_seconds: float
    music_end_seconds: float
    experience_target: ExperienceState
