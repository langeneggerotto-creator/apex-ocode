from __future__ import annotations

from dataclasses import dataclass

from .models import ExperienceGraph


ALLOWED_EVIDENCE_STATUS = {"VERIFIED", "MEASURED", "INFERRED", "POSSIBLE", "UNKNOWN"}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


def validate_experience_graph(graph: ExperienceGraph) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []

    if graph.duration_seconds <= 0:
        issues.append(ValidationIssue("INVALID_DURATION", "duration_seconds must be > 0"))

    if not graph.transformation.from_state.strip() or not graph.transformation.to_state.strip():
        issues.append(ValidationIssue("MISSING_TRANSFORMATION", "transformation endpoints are required"))

    if not graph.checkpoints:
        issues.append(ValidationIssue("NO_CHECKPOINTS", "at least one checkpoint is required"))
        return tuple(issues)

    ordered = sorted(graph.checkpoints, key=lambda c: (c.t_start, c.t_end))

    if abs(ordered[0].t_start) > 1e-9:
        issues.append(ValidationIssue("TIMELINE_GAP", "first checkpoint must start at 0"))

    previous_end = 0.0
    for index, checkpoint in enumerate(ordered):
        if checkpoint.t_start < 0 or checkpoint.t_end <= checkpoint.t_start:
            issues.append(ValidationIssue("INVALID_INTERVAL", f"checkpoint {index} has an invalid interval"))
        if not 0.0 <= checkpoint.intensity <= 1.0:
            issues.append(ValidationIssue("INVALID_INTENSITY", f"checkpoint {index} intensity must be within 0..1"))
        if checkpoint.evidence_status not in ALLOWED_EVIDENCE_STATUS:
            issues.append(ValidationIssue("INVALID_EVIDENCE_STATUS", f"checkpoint {index} has invalid evidence_status"))
        if index > 0:
            if checkpoint.t_start > previous_end + 1e-9:
                issues.append(ValidationIssue("TIMELINE_GAP", f"gap before checkpoint {index}"))
            elif checkpoint.t_start < previous_end - 1e-9:
                issues.append(ValidationIssue("TIMELINE_OVERLAP", f"overlap at checkpoint {index}"))
        previous_end = checkpoint.t_end

    if abs(previous_end - graph.duration_seconds) > 1e-9:
        issues.append(ValidationIssue("TIMELINE_COVERAGE", "checkpoint coverage must end exactly at duration_seconds"))

    for index, checkpoint in enumerate(ordered):
        if checkpoint.intended_inference and checkpoint.intended_inference in checkpoint.prohibited_inference:
            issues.append(ValidationIssue("CONTRADICTORY_CHECKPOINT", f"checkpoint {index} both intends and prohibits the same inference"))

    return tuple(issues)


def assert_valid_experience_graph(graph: ExperienceGraph) -> None:
    issues = validate_experience_graph(graph)
    if issues:
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(detail)
