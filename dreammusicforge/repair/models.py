"""Typed domain model for Release 0.10 -- "failed candidate produces a
bounded repair plan" (spec section 19's acceptance test for this
release).

`VerificationResult` matches spec section 6.11's worked example
(metrics, critical_failures, overall_score, decision, repair) field for
field. `Defect` matches section 8.9's worked example (type, severity,
location, recommendations).

REPAIR_ACTIONS is seeded with section 8.9's six named actions
(cut_away_before_defect, insert_symbolic_detail, replace_local_region,
shorten_shot, use_light_flash, regenerate) but is NOT a closed enum --
section 6.11's own worked example uses `dedicated_lip_sync_pass`, an
action not in section 8.9's list at all. The spec shows two different
repair-action vocabularies in its own two examples; treating either as
exhaustive would be inventing a closed list the spec itself doesn't
commit to. `Defect.recommendations` and `RepairPlan.action` are
therefore validated as non-empty strings, not membership in a fixed set
-- REPAIR_ACTIONS exists as this release's own default vocabulary for
`repair/repair_planner.py`'s classifier to draw from, not a schema
constraint.

SEVERITY_LEVELS is this release's own choice (spec section 8.9 shows
only one example value, "high") -- ordered low/medium/high/critical is
a conventional four-level scale, not a spec-given closed list either,
but *is* enforced as a schema constraint here since defect severity
needs a comparable ordering for the ranking logic in section 8.10
("A beautiful candidate with a critical continuity failure must rank
below a less beautiful candidate that preserves the canonical film").

Same to_dict()/from_dict() convention as the rest of this repo's domain
models -- frozen dataclasses, not the JSON-Schema-in-a-dict pattern used
elsewhere in this repo's sibling dreammusicforge module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

REPAIR_ACTIONS = (
    "cut_away_before_defect", "insert_symbolic_detail", "replace_local_region",
    "shorten_shot", "use_light_flash", "regenerate",
)

SEVERITY_LEVELS = ("low", "medium", "high", "critical")

DECISION_VALUES = ("accept", "reject")


@dataclass(frozen=True)
class Defect:
    id: str
    type: str
    severity: str
    shot_id: str
    recommendations: tuple[str, ...]
    start_seconds: float | None = None
    end_seconds: float | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity,
            "location": {"shot_id": self.shot_id, "start": self.start_seconds, "end": self.end_seconds},
            "recommendations": list(self.recommendations),
        }

    @staticmethod
    def from_dict(data: dict) -> "Defect":
        location = data.get("location", {})
        return Defect(
            id=data["id"],
            type=data["type"],
            severity=data["severity"],
            shot_id=location["shot_id"],
            start_seconds=location.get("start"),
            end_seconds=location.get("end"),
            recommendations=tuple(data.get("recommendations", [])),
        )


@dataclass(frozen=True)
class RepairPlan:
    shot_id: str
    action: str
    preserve: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {"shot_id": self.shot_id, "action": self.action, "preserve": list(self.preserve)}

    @staticmethod
    def from_dict(data: dict) -> "RepairPlan":
        return RepairPlan(shot_id=data["shot_id"], action=data["action"], preserve=tuple(data.get("preserve", [])))


@dataclass(frozen=True)
class VerificationResult:
    candidate_id: str
    metrics: dict[str, float]
    critical_failures: tuple[str, ...]
    overall_score: float
    decision: str
    defects: tuple[Defect, ...] = field(default_factory=tuple)
    repair: RepairPlan | None = None

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "metrics": dict(self.metrics),
            "critical_failures": list(self.critical_failures),
            "overall_score": self.overall_score,
            "decision": self.decision,
            "defects": [defect.to_dict() for defect in self.defects],
            "repair": self.repair.to_dict() if self.repair is not None else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "VerificationResult":
        repair = data.get("repair")
        return VerificationResult(
            candidate_id=data["candidate_id"],
            metrics=dict(data.get("metrics", {})),
            critical_failures=tuple(data.get("critical_failures", [])),
            overall_score=float(data["overall_score"]),
            decision=data["decision"],
            defects=tuple(Defect.from_dict(item) for item in data.get("defects", [])),
            repair=RepairPlan.from_dict(repair) if repair is not None else None,
        )
