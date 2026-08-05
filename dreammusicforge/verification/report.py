"""generate_technical_report(): the top-level orchestration that turns a
rendered candidate file into an objective technical report -- this
release's acceptance test from spec section 19: "objective technical
report generated from video files."

Combines every other module in this package: inspect_media() (media
inspection), a duration/frame-rate tolerance check, measure_audio_rms()
(when the file has audio), and -- when a previous shot's end frame is
supplied -- extract_frame() plus compare_seam() and measure_color_shift()
against it (spec section 9.2's boundary checks). Every value in the
resulting report is measured from the real file, never asserted.
"""
from __future__ import annotations

from pathlib import Path

from .audio import measure_audio_rms
from .color import measure_color_shift
from .errors import TechnicalVerificationError
from .frames import extract_frame
from .inspector import inspect_media
from .models import AudioRmsReport, ColorShiftReport, DurationFrameRateCheck, SeamComparison, TechnicalReport
from .schema import validate_technical_report_schema
from .seam import compare_seam

DEFAULT_DURATION_TOLERANCE_SECONDS = 0.5
DEFAULT_FRAME_RATE_TOLERANCE = 0.5


def generate_technical_report(
    candidate_id: str,
    file_path: Path,
    expected_duration_seconds: float,
    expected_frame_rate: float,
    duration_tolerance_seconds: float = DEFAULT_DURATION_TOLERANCE_SECONDS,
    frame_rate_tolerance: float = DEFAULT_FRAME_RATE_TOLERANCE,
    require_audio: bool = True,
    previous_end_frame_path: Path | None = None,
    frame_extraction_dir: Path | None = None,
) -> TechnicalReport:
    media = inspect_media(file_path)

    duration_diff = abs(media.duration_seconds - expected_duration_seconds)
    frame_rate_diff = abs(media.frame_rate - expected_frame_rate)
    duration_check = DurationFrameRateCheck(
        expected_duration_seconds=expected_duration_seconds,
        measured_duration_seconds=media.duration_seconds,
        expected_frame_rate=expected_frame_rate,
        measured_frame_rate=media.frame_rate,
        duration_tolerance_seconds=duration_tolerance_seconds,
        frame_rate_tolerance=frame_rate_tolerance,
        within_tolerance=duration_diff <= duration_tolerance_seconds and frame_rate_diff <= frame_rate_tolerance,
    )

    failures: list[str] = []
    if not duration_check.within_tolerance:
        failures.append(
            f"duration_frame_rate: measured duration {media.duration_seconds}s / frame_rate {media.frame_rate} "
            f"outside tolerance of expected {expected_duration_seconds}s / {expected_frame_rate}"
        )

    audio_rms: AudioRmsReport | None = None
    if media.has_audio:
        audio_rms = measure_audio_rms(file_path)
        if audio_rms.silent:
            failures.append(f"audio: silent (RMS level {audio_rms.rms_level_db} dB)")
    elif require_audio:
        failures.append("audio: expected but missing from this candidate")

    seam_comparison: SeamComparison | None = None
    color_shift: ColorShiftReport | None = None
    if previous_end_frame_path is not None:
        if frame_extraction_dir is None:
            raise TechnicalVerificationError(["frame_extraction_dir is required when previous_end_frame_path is given"])
        first_frame_path = frame_extraction_dir / f"{candidate_id}-first-frame.png"
        extract_frame(file_path, 0.0, first_frame_path)

        seam_comparison = compare_seam(previous_end_frame_path, first_frame_path)
        if not seam_comparison.similar:
            failures.append(f"seam: dissimilar to previous shot's end frame (SSIM {seam_comparison.ssim_score})")

        color_shift = measure_color_shift(previous_end_frame_path, first_frame_path)
        if color_shift.shifted:
            failures.append(
                f"color: shifted from previous shot's end frame "
                f"(delta_y={color_shift.delta_y}, delta_u={color_shift.delta_u}, delta_v={color_shift.delta_v})"
            )

    report = TechnicalReport(
        candidate_id=candidate_id, file=str(file_path), media=media, duration_frame_rate_check=duration_check,
        audio_rms=audio_rms, seam_comparison=seam_comparison, color_shift=color_shift,
        passed=not failures, failures=tuple(failures),
    )

    errors = validate_technical_report_schema(report.to_dict())
    if errors:
        raise TechnicalVerificationError(errors)
    return report
