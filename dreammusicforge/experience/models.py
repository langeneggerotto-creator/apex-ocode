from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class Transformation:
    from_state: str
    to_state: str


@dataclass(frozen=True)
class ExperienceCheckpoint:
    t_start: float
    t_end: float
    primary_experience: str
    intensity: float
    attention_goal: str
    memory_goal: str
    intended_inference: str
    secondary_experiences: tuple[str, ...] = field(default_factory=tuple)
    prohibited_inference: tuple[str, ...] = field(default_factory=tuple)
    evidence_status: str = "UNKNOWN"


@dataclass(frozen=True)
class ExperienceGraph:
    version: str
    duration_seconds: float
    transformation: Transformation
    checkpoints: tuple[ExperienceCheckpoint, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
