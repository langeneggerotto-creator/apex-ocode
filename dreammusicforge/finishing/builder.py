"""finish_film(): the top-level orchestration -- takes an already
assembled film (Release 0.11's ExportManifest.output_file) and applies
a real loudness normalization pass plus an optional color adjustment
pass, returning a typed, hash-traceable FinishingResult.

`target_lufs` defaults to -14.0, a commonly cited streaming-platform
loudness target (Spotify/YouTube) -- this is an industry-standard
default, not a number taken from the original spec text (which this
session no longer has access to; see models.py's module docstring).

This release measures the *result's* actual loudness after
normalizing rather than trusting the requested target blindly (the
`measured_loudness` field on FinishingResult is real, not the
requested value echoed back) -- but does not fail closed if the
single-pass `loudnorm` result lands a little off-target, since ffmpeg's
single-pass mode is a real, disclosed estimate, not a promise; a
production-grade finishing pass would want the more accurate two-pass
sequence, which is out of this release's scope (see the README).
"""
from __future__ import annotations

from pathlib import Path

from ..assembly.models import ExportManifest
from ..core.hashing import hash_file
from ..verification.inspector import inspect_media
from .errors import FinishingError
from .ids import generate_finishing_result_id
from .models import ColorAdjustment, FinishingResult
from .pipeline import adjust_color, measure_loudness, normalize_loudness
from .schema import validate_finishing_result_schema

DEFAULT_TARGET_LUFS = -14.0


def finish_film(
    export_manifest: ExportManifest,
    work_dir: Path,
    target_lufs: float = DEFAULT_TARGET_LUFS,
    color_adjustment: ColorAdjustment | None = None,
    result_id: str | None = None,
) -> FinishingResult:
    source_path = Path(export_manifest.output_file)
    if not source_path.exists():
        raise FinishingError([f"export_manifest.output_file {str(source_path)!r} does not exist"])

    work_dir.mkdir(parents=True, exist_ok=True)
    loudness_path = work_dir / "loudness-normalized.mp4"
    normalize_loudness(source_path, loudness_path, target_lufs)

    applied_color_adjustment = color_adjustment or ColorAdjustment()
    if applied_color_adjustment.is_identity():
        final_path = loudness_path
    else:
        final_path = work_dir / "color-adjusted.mp4"
        adjust_color(loudness_path, final_path, applied_color_adjustment)

    measured_loudness = measure_loudness(final_path)
    media = inspect_media(final_path)

    result = FinishingResult(
        id=result_id or generate_finishing_result_id(),
        source_file=str(source_path),
        output_file=str(final_path),
        output_hash=hash_file(final_path),
        target_lufs=target_lufs,
        measured_loudness=measured_loudness,
        color_adjustment=applied_color_adjustment,
        duration_seconds=media.duration_seconds,
    )

    validation_errors = validate_finishing_result_schema(result.to_dict())
    if validation_errors:
        raise FinishingError(validation_errors)
    return result
