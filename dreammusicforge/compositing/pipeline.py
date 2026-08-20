"""composite_layers(): thin, typed wrapper over
compositing/ffmpeg_runner.py's argv-construction."""
from __future__ import annotations

from pathlib import Path

from .ffmpeg_runner import run_ffmpeg_composite
from .models import CompositeLayer


def composite_layers(background: CompositeLayer, foreground: CompositeLayer, output_path: Path) -> Path:
    run_ffmpeg_composite(
        Path(background.source_file), Path(foreground.source_file), output_path,
        mask_type=foreground.mask_type, chroma_color=foreground.chroma_color,
        chroma_similarity=foreground.chroma_similarity, chroma_blend=foreground.chroma_blend,
    )
    return output_path
