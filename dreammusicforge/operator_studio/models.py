"""Typed domain model for Release 0.15 -- Operator Studio.

Not verified against the original spec's own section text for this
release (only the release name, "Operator Studio," survived this
session's context compaction, same gap as Releases 0.12-0.14) -- this
release's README section calls it "a web interface" from an earlier
release's own forward reference, which is the only scope hint that
survived. Interpreted here as a read-only human-review status board
over data this session's earlier releases already produce
(`VerificationResult` from Release 0.10, `ExportManifest` from Release
0.11, `FinishingResult` from Release 0.14) -- not a live dashboard
backed by a real database, since no persistence layer exists anywhere
in this codebase yet (every release since 0.2 has named that gap
explicitly).

OperatorReport is an immutable snapshot: a caller assembles it from
whatever typed results it currently holds in memory and hands it to
operator_studio/render.py or operator_studio/server.py. It does not
refresh itself and does not read from any store -- rebuilding it for a
new snapshot is the caller's job.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..assembly.models import ExportManifest
from ..finishing.models import FinishingResult
from ..repair.models import VerificationResult


@dataclass(frozen=True)
class OperatorReport:
    id: str
    generated_at: str
    verification_results: tuple[VerificationResult, ...] = field(default_factory=tuple)
    export_manifests: tuple[ExportManifest, ...] = field(default_factory=tuple)
    finishing_results: tuple[FinishingResult, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "generated_at": self.generated_at,
            "verification_results": [item.to_dict() for item in self.verification_results],
            "export_manifests": [item.to_dict() for item in self.export_manifests],
            "finishing_results": [item.to_dict() for item in self.finishing_results],
        }

    @staticmethod
    def from_dict(data: dict) -> "OperatorReport":
        return OperatorReport(
            id=data["id"],
            generated_at=data["generated_at"],
            verification_results=tuple(VerificationResult.from_dict(item) for item in data.get("verification_results", [])),
            export_manifests=tuple(ExportManifest.from_dict(item) for item in data.get("export_manifests", [])),
            finishing_results=tuple(FinishingResult.from_dict(item) for item in data.get("finishing_results", [])),
        )
