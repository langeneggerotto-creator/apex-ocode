"""evaluate_candidate(): the accept/reject workflow -- this release's
fourth "Build" deliverable and the function the acceptance test runs
through: "failed candidate produces a bounded repair plan."

A candidate with zero defects is accepted with no repair plan. A
candidate with one or more defects is rejected; `build_repair_plan()`
then produces exactly one action bounded to exactly one shot (spec
section 19's "bounded"): multiple simultaneous defects, or any defect
whose top recommendation is itself "regenerate", collapse to a single
`regenerate` action rather than a list of partial fixes attempted
together -- a shot with three things wrong gets regenerated once, not
patched three times. `preserve` names every metric that passed, so the
repair instruction states what must NOT change, matching spec section
6.11's own worked example (`preserve: [identity, costume, camera,
world]` alongside a `dedicated_lip_sync_pass` repair).
"""
from __future__ import annotations

from .classifier import classify_failures
from .errors import AcceptanceRepairError
from .models import Defect, RepairPlan, VerificationResult
from .schema import validate_verification_result_schema


def build_repair_plan(defects: tuple[Defect, ...], metrics: dict[str, float], shot_id: str) -> RepairPlan:
    top_recommendations = [defect.recommendations[0] for defect in defects if defect.recommendations]
    if len(defects) > 1 or "regenerate" in top_recommendations:
        action = "regenerate"
    else:
        action = top_recommendations[0]

    failed_metric_names = {defect.type for defect in defects}
    preserve = tuple(name for name in metrics if name not in failed_metric_names)

    return RepairPlan(shot_id=shot_id, action=action, preserve=preserve)


def evaluate_candidate(
    candidate_id: str,
    shot_id: str,
    metrics: dict[str, float],
    thresholds: dict[str, float] | None = None,
) -> VerificationResult:
    defects = classify_failures(metrics, shot_id, thresholds)
    critical_failures = tuple(defect.type for defect in defects)
    overall_score = sum(metrics.values()) / len(metrics) if metrics else 0.0
    decision = "reject" if defects else "accept"
    repair = build_repair_plan(defects, metrics, shot_id) if defects else None

    result = VerificationResult(
        candidate_id=candidate_id, metrics=metrics, critical_failures=critical_failures,
        overall_score=overall_score, decision=decision, defects=defects, repair=repair,
    )

    errors = validate_verification_result_schema(result.to_dict())
    if errors:
        raise AcceptanceRepairError(errors)
    return result
