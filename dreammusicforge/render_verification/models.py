from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VerificationDecision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    REVIEW = "REVIEW"


@dataclass(frozen=True)
class RenderCandidate:
    candidate_id: str
    package_id: str
    file_name: str
    sha256: str
    duration_seconds: float
    width: int
    height: int
    fps: float
    has_video: bool = True
    has_audio: bool = True

    def validate(self) -> None:
        if not self.candidate_id.strip() or not self.package_id.strip():
            raise ValueError("candidate_id and package_id are required")
        if not self.file_name.strip() or not self.sha256.strip():
            raise ValueError("file_name and sha256 are required")
        if self.duration_seconds <= 0 or self.width <= 0 or self.height <= 0 or self.fps <= 0:
            raise ValueError("media dimensions, duration and fps must be positive")
        if not self.has_video:
            raise ValueError("candidate must contain video")


@dataclass(frozen=True)
class MetricResult:
    name: str
    score: float | None
    passed: bool | None
    critical: bool
    evidence: str

    def validate(self) -> None:
        if not self.name.strip() or not self.evidence.strip():
            raise ValueError("metric name and evidence are required")
        if self.score is not None and not 0.0 <= self.score <= 100.0:
            raise ValueError("metric score must be between 0 and 100")


@dataclass(frozen=True)
class VerificationReport:
    candidate_id: str
    package_id: str
    decision: VerificationDecision
    metrics: tuple[MetricResult, ...]
    critical_failures: tuple[str, ...]
    unresolved_gates: tuple[str, ...]
    reasons: tuple[str, ...]

    def validate(self) -> None:
        if not self.candidate_id.strip() or not self.package_id.strip():
            raise ValueError("report identifiers are required")
        if not self.metrics:
            raise ValueError("verification report requires metrics")
        for metric in self.metrics:
            metric.validate()
        if self.decision is VerificationDecision.ACCEPT and (self.critical_failures or self.unresolved_gates):
            raise ValueError("accepted candidate cannot have critical failures or unresolved gates")
