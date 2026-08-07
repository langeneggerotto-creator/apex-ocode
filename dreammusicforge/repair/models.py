from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RepairAction(str, Enum):
    REGENERATE = "REGENERATE"
    RELIP_SYNC = "RELIP_SYNC"
    REPLACE_LAYER = "REPLACE_LAYER"
    SHORTEN_SHOT = "SHORTEN_SHOT"
    EDITORIAL_CONCEALMENT = "EDITORIAL_CONCEALMENT"
    REDESIGN_TASK = "REDESIGN_TASK"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass(frozen=True)
class RepairContract:
    repair_id: str
    candidate_id: str
    package_id: str
    action: RepairAction
    preserve_metrics: tuple[str, ...]
    change_metrics: tuple[str, ...]
    instructions: tuple[str, ...]
    critical_failures: tuple[str, ...]
    unresolved_gates: tuple[str, ...]

    def validate(self) -> None:
        if not self.repair_id.strip() or not self.candidate_id.strip() or not self.package_id.strip():
            raise ValueError("repair identifiers are required")
        if not self.change_metrics and self.action is not RepairAction.MANUAL_REVIEW:
            raise ValueError("repair must declare at least one changed metric")
        overlap = set(self.preserve_metrics) & set(self.change_metrics)
        if overlap:
            raise ValueError(f"metrics cannot be both preserved and changed: {sorted(overlap)}")
        if not self.instructions:
            raise ValueError("repair instructions are required")
