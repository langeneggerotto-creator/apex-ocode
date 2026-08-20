"""build_composite(): the top-level orchestration -- takes one
background CompositeLayer and one foreground CompositeLayer, runs
them through real ffmpeg compositing, and returns a typed, hash-
traceable CompositeResult.

Fails closed: a foreground layer whose mask_type isn't in
EXECUTABLE_MASK_TYPES (only "chromakey" and "none" are) raises rather
than silently falling back to a plain overlay -- same discipline
assembly/builder.py applies to transitions it can't yet execute.
"""
from __future__ import annotations

from pathlib import Path

from ..core.hashing import hash_file
from ..verification.inspector import inspect_media
from .errors import CompositingError
from .ids import generate_composite_id
from .models import EXECUTABLE_MASK_TYPES, CompositeLayer, CompositeResult
from .pipeline import composite_layers
from .schema import validate_composite_result_schema


def build_composite(
    shot_id: str,
    background: CompositeLayer,
    foreground: CompositeLayer,
    work_dir: Path,
    output_path: Path | None = None,
    result_id: str | None = None,
) -> CompositeResult:
    errors: list[str] = []
    if background.layer_type != "background":
        errors.append(f"background layer must have layer_type 'background', got {background.layer_type!r}")
    if foreground.layer_type != "foreground":
        errors.append(f"foreground layer must have layer_type 'foreground', got {foreground.layer_type!r}")
    if foreground.mask_type not in EXECUTABLE_MASK_TYPES:
        errors.append(
            f"mask_type {foreground.mask_type!r} is not executed by this release "
            f"(only {EXECUTABLE_MASK_TYPES} are) -- refusing to silently fall back to a plain overlay"
        )
    if errors:
        raise CompositingError(errors)

    work_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_path or (work_dir / f"{shot_id}-composite.mp4")
    composite_layers(background, foreground, output_path)

    media = inspect_media(output_path)
    result = CompositeResult(
        id=result_id or generate_composite_id(),
        shot_id=shot_id,
        output_file=str(output_path),
        output_hash=hash_file(output_path),
        width=media.width,
        height=media.height,
        duration_seconds=media.duration_seconds,
        layers=(background, foreground),
    )

    validation_errors = validate_composite_result_schema(result.to_dict())
    if validation_errors:
        raise CompositingError(validation_errors)
    return result
