from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from .models import ExecutionEvidence, ExecutionStatus, MediaExecutionPlan


_ALLOWED_BINARIES = {"ffmpeg"}
_ALLOWED_OPERATIONS = {"NORMALIZE_VIDEO", "CONCAT_VIDEO", "MASTER_AUDIO_LAYBACK"}


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def execute_media_plan(plan: MediaExecutionPlan, workspace: Path, *, dry_run: bool = True) -> ExecutionEvidence:
    plan.validate()
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    executed: list[str] = []

    for step in plan.steps:
        step.validate()
        if step.operation not in _ALLOWED_OPERATIONS:
            raise ValueError(f"operation not allowlisted: {step.operation}")
        if step.command[0] not in _ALLOWED_BINARIES:
            raise ValueError("only ffmpeg is allowlisted")
        if dry_run:
            executed.append(step.step_id)
            continue
        try:
            completed = subprocess.run(step.command, cwd=workspace, capture_output=True, text=True, check=False)
        except OSError as exc:
            return ExecutionEvidence(plan.plan_id, ExecutionStatus.FAILED, plan.final_output_file, None, tuple(executed), step.step_id, str(exc))
        if completed.returncode != 0:
            return ExecutionEvidence(plan.plan_id, ExecutionStatus.FAILED, plan.final_output_file, None, tuple(executed), step.step_id, completed.stderr[-4000:])
        executed.append(step.step_id)

    if dry_run:
        return ExecutionEvidence(plan.plan_id, ExecutionStatus.PLANNED, plan.final_output_file, None, tuple(executed))

    output = workspace / plan.final_output_file
    if not output.exists():
        return ExecutionEvidence(plan.plan_id, ExecutionStatus.FAILED, plan.final_output_file, None, tuple(executed), "final-output", "final output missing")
    evidence = ExecutionEvidence(plan.plan_id, ExecutionStatus.EXECUTED, plan.final_output_file, _hash_file(output), tuple(executed))
    evidence.validate()
    return evidence
