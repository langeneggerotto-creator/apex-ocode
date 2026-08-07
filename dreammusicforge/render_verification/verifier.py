from __future__ import annotations

from dataclasses import replace

from dreammusicforge.providers.kling.models import KlingExecutionPackage
from .models import MetricResult, RenderCandidate, VerificationDecision, VerificationReport


def verify_candidate(
    candidate: RenderCandidate,
    package: KlingExecutionPackage,
    measured_metrics: tuple[MetricResult, ...],
    duration_tolerance_seconds: float = 0.25,
) -> VerificationReport:
    candidate.validate()
    package.validate()
    if candidate.package_id != package.package_id:
        raise ValueError("candidate package_id does not match execution package")
    if duration_tolerance_seconds < 0:
        raise ValueError("duration_tolerance_seconds must be non-negative")

    metrics = list(measured_metrics)
    duration_delta = abs(candidate.duration_seconds - package.duration_seconds)
    metrics.append(
        MetricResult(
            name="duration",
            score=max(0.0, 100.0 - duration_delta * 20.0),
            passed=duration_delta <= duration_tolerance_seconds,
            critical=True,
            evidence=f"candidate={candidate.duration_seconds:.3f}s expected={package.duration_seconds:.3f}s",
        )
    )
    metrics.append(
        MetricResult(
            name="technical_validity",
            score=100.0 if candidate.has_video else 0.0,
            passed=candidate.has_video,
            critical=True,
            evidence=f"video={candidate.has_video} {candidate.width}x{candidate.height} fps={candidate.fps}",
        )
    )

    by_name = {metric.name: metric for metric in metrics}
    required = tuple(package.acceptance_gates)
    unresolved = tuple(gate for gate in required if gate not in by_name)
    failures = tuple(
        metric.name
        for metric in metrics
        if metric.critical and metric.passed is False
    )

    if failures:
        decision = VerificationDecision.REJECT
        reasons = tuple(f"critical gate failed: {name}" for name in failures)
    elif unresolved:
        decision = VerificationDecision.REVIEW
        reasons = tuple(f"required gate unresolved: {name}" for name in unresolved)
    else:
        decision = VerificationDecision.ACCEPT
        reasons = ("all required acceptance gates resolved without critical failure",)

    report = VerificationReport(
        candidate_id=candidate.candidate_id,
        package_id=package.package_id,
        decision=decision,
        metrics=tuple(metrics),
        critical_failures=failures,
        unresolved_gates=unresolved,
        reasons=reasons,
    )
    report.validate()
    return report
