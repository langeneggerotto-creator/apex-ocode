"""Job: one execution of a task or ad-hoc command, and its state machine.

The seven states are exactly the ones ``FULL_PLATFORM_SPEC.md`` §9 names:
queued, leased, running, succeeded, failed, cancelled, timed-out. Transitions are
validated explicitly — an invalid transition (e.g. trying to move a job that
already reached a terminal state) raises rather than being silently accepted,
since a job manager silently allowing that could corrupt evidence and status
reporting.
"""

from __future__ import annotations

import dataclasses
import enum
import time
import uuid
from typing import Any, Dict, List, Optional


class JobState(str, enum.Enum):
    QUEUED = "queued"
    LEASED = "leased"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


TERMINAL_STATES = {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED, JobState.TIMED_OUT}

_ALLOWED_TRANSITIONS: Dict[JobState, set] = {
    JobState.QUEUED: {JobState.LEASED, JobState.CANCELLED},
    # LEASED -> FAILED covers a job whose sandboxed process never actually
    # started (e.g. the workspace trust check or a seccomp-availability check
    # failed) — it never reached RUNNING at all, so FAILED is a direct sibling
    # transition from LEASED, not something that has to pass through RUNNING.
    JobState.LEASED: {JobState.RUNNING, JobState.CANCELLED, JobState.FAILED},
    JobState.RUNNING: {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED, JobState.TIMED_OUT},
    JobState.SUCCEEDED: set(),
    JobState.FAILED: set(),
    JobState.CANCELLED: set(),
    JobState.TIMED_OUT: set(),
}


class InvalidTransitionError(RuntimeError):
    pass


def new_job_id() -> str:
    return uuid.uuid4().hex[:16]


@dataclasses.dataclass
class Job:
    job_id: str
    task_name: Optional[str]
    command: List[str]
    workspace: str
    timeout_seconds: int
    state: JobState = JobState.QUEUED
    submitted_at: float = dataclasses.field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    exit_code: Optional[int] = None
    controls_applied: Optional[Dict[str, Any]] = None
    resource_usage: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def transition(self, new_state: JobState) -> None:
        allowed = _ALLOWED_TRANSITIONS[self.state]
        if new_state not in allowed:
            raise InvalidTransitionError(f"cannot move job {self.job_id} from {self.state} to {new_state}")
        if new_state == JobState.RUNNING:
            self.started_at = time.time()
        if new_state in TERMINAL_STATES:
            self.finished_at = time.time()
        self.state = new_state

    def to_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d["state"] = self.state.value
        return d
