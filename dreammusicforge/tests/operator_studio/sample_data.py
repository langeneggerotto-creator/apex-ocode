"""Shared sample typed objects for operator_studio tests -- no ffmpeg
needed, this package only renders/serves data other releases already
produce."""
from __future__ import annotations

from dreammusicforge.assembly.models import AssembledClip, ExportManifest
from dreammusicforge.finishing.models import ColorAdjustment, FinishingResult, LoudnessReport
from dreammusicforge.repair.models import RepairPlan, VerificationResult

ACCEPTED_RESULT = VerificationResult(
    candidate_id="CANDIDATE-accepted", metrics={"identity": 96.0}, critical_failures=(),
    overall_score=96.0, decision="accept",
)

REJECTED_RESULT = VerificationResult(
    candidate_id="CANDIDATE-rejected", metrics={"continuity": 20.0}, critical_failures=("continuity",),
    overall_score=20.0, decision="reject",
    repair=RepairPlan(shot_id="SHOT-1", action="regenerate"),
)

SAMPLE_EXPORT_MANIFEST = ExportManifest(
    id="EXPORT-deadbeef", master_song_id="AUDIO-sample", master_song_hash="a" * 64,
    output_file="/tmp/sample.mp4", output_hash="b" * 64, total_duration_seconds=30.0,
    created_at="2026-08-06T00:00:00+00:00",
    clips=(AssembledClip(candidate_id="CANDIDATE-accepted", shot_id="SHOT-1", source_hash="c" * 64, start_seconds_in_final=0.0, normalized_duration_seconds=30.0),),
)

SAMPLE_FINISHING_RESULT = FinishingResult(
    id="FINISHING-deadbeef", source_file="/tmp/sample.mp4", output_file="/tmp/sample-finished.mp4",
    output_hash="d" * 64, target_lufs=-14.0,
    measured_loudness=LoudnessReport(integrated_lufs=-14.1, true_peak_dbfs=-1.2, loudness_range_lu=5.0),
    color_adjustment=ColorAdjustment(), duration_seconds=30.0,
)
