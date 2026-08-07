from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionStatus(str, Enum):
    PLANNED = "PLANNED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class MediaExecutionStep:
    step_id: str
    operation: str
    command: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]

    def validate(self) -> None:
        if not self.step_id.strip() or not self.operation.strip():
            raise ValueError("step_id and operation are required")
        if not self.command:
            raise ValueError("execution command is required")
        if not self.outputs:
            raise ValueError("execution step requires output")


@dataclass(frozen=True)
class MediaExecutionPlan:
    plan_id: str
    manifest_id: str
    steps: tuple[MediaExecutionStep, ...]
    final_output_file: str
    master_audio_file: str
    mute_provider_audio: bool

    def validate(self) -> None:
        if not self.plan_id.strip() or not self.manifest_id.strip():
            raise ValueError("plan identifiers are required")
        if not self.steps:
            raise ValueError("media execution plan requires steps")
        if not self.final_output_file.strip() or not self.master_audio_file.strip():
            raise ValueError("final output and master audio are required")
        for step in self.steps:
            step.validate()


@dataclass(frozen=True)
class ExecutionEvidence:
    plan_id: str
    status: ExecutionStatus
    output_file: str
    sha256: str | None
    executed_steps: tuple[str, ...]
    failed_step: str | None = None
    stderr: str | None = None

    def validate(self) -> None:
        if not self.plan_id.strip() or not self.output_file.strip():
            raise ValueError("execution evidence identifiers are required")
        if self.status is ExecutionStatus.EXECUTED and not self.sha256:
            raise ValueError("executed output requires sha256")
        if self.status is ExecutionStatus.FAILED and not self.failed_step:
            raise ValueError("failed execution requires failed_step")
