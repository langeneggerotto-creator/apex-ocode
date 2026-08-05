"""MediaMetadata / DurationFrameRateCheck / AudioRmsReport /
SeamComparison / ColorShiftReport / TechnicalReport JSON schema
contracts.

Same dependency-free, dict-shaped, hand-walked convention as every
sibling package's schema.py -- no `jsonschema` package. Each
validate_*_schema() function returns every error found, not just the
first; empty list means valid.
"""
from __future__ import annotations


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_media_metadata_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["media_metadata must be a JSON object"]

    for field_name in ("duration_seconds", "frame_rate", "width", "height", "video_codec", "has_audio"):
        if field_name not in data:
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not _is_number(data["duration_seconds"]) or data["duration_seconds"] <= 0:
        errors.append("media_metadata duration_seconds must be a positive number")
    if not _is_number(data["frame_rate"]) or data["frame_rate"] <= 0:
        errors.append("media_metadata frame_rate must be a positive number")
    for field_name in ("width", "height"):
        value = data[field_name]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"media_metadata {field_name} must be a positive integer")
    if not _is_non_empty_str(data["video_codec"]):
        errors.append("media_metadata video_codec must be a non-empty string")
    if not isinstance(data["has_audio"], bool):
        errors.append("media_metadata has_audio must be a boolean")

    audio_codec = data.get("audio_codec")
    if audio_codec is not None and not _is_non_empty_str(audio_codec):
        errors.append("media_metadata audio_codec, if present, must be a non-empty string or null")
    if data.get("has_audio") is True and audio_codec is None:
        errors.append("media_metadata has_audio is true but audio_codec is null")

    return errors


def validate_duration_frame_rate_check_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["duration_frame_rate_check must be a JSON object"]

    required = (
        "expected_duration_seconds", "measured_duration_seconds", "expected_frame_rate",
        "measured_frame_rate", "duration_tolerance_seconds", "frame_rate_tolerance", "within_tolerance",
    )
    for field_name in required:
        if field_name not in data:
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    for field_name in required[:-1]:
        if not _is_number(data[field_name]) or data[field_name] < 0:
            errors.append(f"duration_frame_rate_check {field_name} must be a non-negative number")
    if not isinstance(data["within_tolerance"], bool):
        errors.append("duration_frame_rate_check within_tolerance must be a boolean")

    return errors


def validate_audio_rms_report_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["audio_rms_report must be a JSON object"]
    for field_name in ("rms_level_db", "peak_level_db"):
        if field_name not in data or not _is_number(data[field_name]):
            errors.append(f"audio_rms_report {field_name} must be a number")
    if "silent" not in data or not isinstance(data["silent"], bool):
        errors.append("audio_rms_report silent must be a boolean")
    return errors


def validate_seam_comparison_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["seam_comparison must be a JSON object"]
    value = data.get("ssim_score")
    if not _is_number(value) or not (0.0 <= value <= 1.0):
        errors.append("seam_comparison ssim_score must be a number in [0, 1]")
    if "similar" not in data or not isinstance(data["similar"], bool):
        errors.append("seam_comparison similar must be a boolean")
    return errors


def validate_color_shift_report_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["color_shift_report must be a JSON object"]
    for field_name in ("delta_y", "delta_u", "delta_v"):
        if field_name not in data or not _is_number(data[field_name]) or data[field_name] < 0:
            errors.append(f"color_shift_report {field_name} must be a non-negative number")
    if "shifted" not in data or not isinstance(data["shifted"], bool):
        errors.append("color_shift_report shifted must be a boolean")
    return errors


def validate_technical_report_schema(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["technical_report must be a JSON object"]

    for field_name in ("candidate_id", "file", "media", "duration_frame_rate_check", "passed"):
        if field_name not in data or data[field_name] in (None, ""):
            errors.append(f"missing required field: {field_name}")
    if errors:
        return errors

    if not _is_non_empty_str(data["candidate_id"]):
        errors.append("technical_report candidate_id must be a non-empty string")
    if not _is_non_empty_str(data["file"]):
        errors.append("technical_report file must be a non-empty string")
    if not isinstance(data["passed"], bool):
        errors.append("technical_report passed must be a boolean")

    errors.extend(f"media: {error}" for error in validate_media_metadata_schema(data["media"]))
    errors.extend(f"duration_frame_rate_check: {error}" for error in validate_duration_frame_rate_check_schema(data["duration_frame_rate_check"]))

    audio_rms = data.get("audio_rms")
    if audio_rms is not None:
        errors.extend(f"audio_rms: {error}" for error in validate_audio_rms_report_schema(audio_rms))
    seam = data.get("seam_comparison")
    if seam is not None:
        errors.extend(f"seam_comparison: {error}" for error in validate_seam_comparison_schema(seam))
    color_shift = data.get("color_shift")
    if color_shift is not None:
        errors.extend(f"color_shift: {error}" for error in validate_color_shift_report_schema(color_shift))

    failures = data.get("failures", [])
    if not isinstance(failures, list) or not all(_is_non_empty_str(item) for item in failures):
        errors.append("technical_report failures, if present, must be a list of non-empty strings")
    elif data["passed"] and failures:
        errors.append("technical_report passed is true but failures is non-empty")
    elif not data["passed"] and not failures:
        errors.append("technical_report passed is false but failures is empty")

    return errors
