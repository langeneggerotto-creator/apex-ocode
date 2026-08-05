"""Typed domain model for Release 0.8 -- "every imported candidate is
traceable" (spec section 19's acceptance test for this release).

Field shapes follow spec section 6.10's `candidate` example YAML, plus
two additions this release's own acceptance test requires that 6.10's
worked example doesn't show: `file_size_bytes` (real filesystem
metadata -- the "metadata" build deliverable, distinct from "media
inspection," which is Release 0.9's job and needs actual stream/codec
parsing this release doesn't do) and `imported_at` (an ISO 8601
timestamp -- without one, "traceable" would mean "traceable to a file,"
not "traceable to a point in time," and every other timestamped entity
in this repository, starting with core/models.py's Project, carries
one). CANDIDATE_VERIFICATION_STATUSES and CANDIDATE_DECISIONS are this
release's own enums, inferred from section 6.10/6.11's example values
("pending", "reject") since the spec doesn't give a closed list.

Same to_dict()/from_dict() convention as the rest of this repo's domain
models -- frozen dataclasses, not the JSON-Schema-in-a-dict pattern used
elsewhere in this repo's sibling dreammusicforge module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CANDIDATE_VERIFICATION_STATUSES = ("pending", "passed", "failed")
CANDIDATE_DECISIONS = ("pending", "accept", "reject")


@dataclass(frozen=True)
class Candidate:
    id: str
    render_task_id: str
    provider: str
    model_version: str
    file: str
    file_size_bytes: int
    prompt_hash: str
    output_hash: str
    imported_at: str
    reference_hashes: tuple[str, ...] = field(default_factory=tuple)
    verification_status: str = "pending"
    decision: str = "pending"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "render_task_id": self.render_task_id,
            "provider": self.provider,
            "model_version": self.model_version,
            "file": self.file,
            "file_size_bytes": self.file_size_bytes,
            "prompt_hash": self.prompt_hash,
            "reference_hashes": list(self.reference_hashes),
            "output_hash": self.output_hash,
            "imported_at": self.imported_at,
            "verification_status": self.verification_status,
            "decision": self.decision,
        }

    @staticmethod
    def from_dict(data: dict) -> "Candidate":
        return Candidate(
            id=data["id"],
            render_task_id=data["render_task_id"],
            provider=data["provider"],
            model_version=data["model_version"],
            file=data["file"],
            file_size_bytes=int(data["file_size_bytes"]),
            prompt_hash=data["prompt_hash"],
            reference_hashes=tuple(data.get("reference_hashes", [])),
            output_hash=data["output_hash"],
            imported_at=data["imported_at"],
            verification_status=data.get("verification_status", "pending"),
            decision=data.get("decision", "pending"),
        )
