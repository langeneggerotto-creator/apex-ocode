"""DreamMusicForge Film Compiler -- verification package (Release 0.9).

Public API:

    from dreammusicforge.verification import (
        MediaMetadata, DurationFrameRateCheck, AudioRmsReport,
        SeamComparison, ColorShiftReport, TechnicalReport,
        inspect_media, extract_frame, compare_seam, measure_audio_rms,
        measure_color_shift, generate_technical_report,
        validate_media_metadata_schema, validate_duration_frame_rate_check_schema,
        validate_audio_rms_report_schema, validate_seam_comparison_schema,
        validate_color_shift_report_schema, validate_technical_report_schema,
        FfmpegNotAvailableError, FfmpegRunError, TechnicalVerificationError,
    )

This is the first package in this repository that depends on an
external binary (ffmpeg/ffprobe) rather than stdlib alone -- see
verification/ffmpeg_runner.py's module docstring for why, and
README.md's "Design choices" section for the full disclosure.

Everything else in the full spec (repair, assembly, lip-sync,
compositing, ...) is later releases and is not present here.
"""
from __future__ import annotations

from .audio import measure_audio_rms
from .color import measure_color_shift
from .errors import FfmpegNotAvailableError, FfmpegRunError, TechnicalVerificationError
from .frames import extract_frame
from .inspector import inspect_media
from .models import AudioRmsReport, ColorShiftReport, DurationFrameRateCheck, MediaMetadata, SeamComparison, TechnicalReport
from .report import generate_technical_report
from .schema import (
    validate_audio_rms_report_schema, validate_color_shift_report_schema,
    validate_duration_frame_rate_check_schema, validate_media_metadata_schema, validate_seam_comparison_schema,
    validate_technical_report_schema,
)
from .seam import compare_seam

__all__ = [
    "AudioRmsReport", "ColorShiftReport", "DurationFrameRateCheck", "FfmpegNotAvailableError", "FfmpegRunError",
    "MediaMetadata", "SeamComparison", "TechnicalReport", "TechnicalVerificationError", "compare_seam",
    "extract_frame", "generate_technical_report", "inspect_media", "measure_audio_rms", "measure_color_shift",
    "validate_audio_rms_report_schema", "validate_color_shift_report_schema",
    "validate_duration_frame_rate_check_schema", "validate_media_metadata_schema", "validate_seam_comparison_schema",
    "validate_technical_report_schema",
]
