"""Typed domain model for Release 0.12 -- Lip-Sync Adapter.

Not verified against the original spec's own section text for this
release (only the release name, "Lip-Sync Adapter," survived this
session's context compaction) -- this shape is this repository's own
design, following the same to_dict()/from_dict() frozen-dataclass
convention as every other package, not a field-for-field transcription
of a spec YAML example the way Releases 0.1-0.11 are.

LipSyncRequest is the typed, evidence-backed unit of work: which shot
needs lip sync, which candidate clip it applies to, and a real audio
window physically extracted (via ffmpeg, lipsync/ffmpeg_runner.py) from
the canonical MasterSong for the shot's exact timing range -- so a real
lip-sync engine has a concrete, traceable file to consume, the same way
providers/kling's KlingPackage is a concrete, traceable unit of work for
a video generator rather than a vague instruction.

LipSyncResult is deliberately allowed to report "not_applied": this
release defines the request contract and performs real audio
extraction, but does not itself run a lip-sync model (no such model is
available in this dependency-free-until-necessary codebase) -- see
lipsync/adapter.py's NullLipSyncAdapter. Claiming "applied" without an
actual engine behind it would violate this repository's rule against
claiming an integration that wasn't run.
"""
from __future__ import annotations

from dataclasses import dataclass

LIP_SYNC_RESULT_STATUSES = ("not_applied", "applied", "failed")


@dataclass(frozen=True)
class LipSyncRequest:
    id: str
    shot_id: str
    candidate_id: str
    source_file: str
    audio_window_file: str
    audio_start_seconds: float
    audio_end_seconds: float

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "shot_id": self.shot_id,
            "candidate_id": self.candidate_id,
            "source_file": self.source_file,
            "audio_window_file": self.audio_window_file,
            "audio_start_seconds": self.audio_start_seconds,
            "audio_end_seconds": self.audio_end_seconds,
        }

    @staticmethod
    def from_dict(data: dict) -> "LipSyncRequest":
        return LipSyncRequest(
            id=data["id"],
            shot_id=data["shot_id"],
            candidate_id=data["candidate_id"],
            source_file=data["source_file"],
            audio_window_file=data["audio_window_file"],
            audio_start_seconds=float(data["audio_start_seconds"]),
            audio_end_seconds=float(data["audio_end_seconds"]),
        )


@dataclass(frozen=True)
class LipSyncResult:
    request_id: str
    status: str
    reason: str
    output_file: str | None = None

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "reason": self.reason,
            "output_file": self.output_file,
        }

    @staticmethod
    def from_dict(data: dict) -> "LipSyncResult":
        return LipSyncResult(
            request_id=data["request_id"],
            status=data["status"],
            reason=data["reason"],
            output_file=data.get("output_file"),
        )
