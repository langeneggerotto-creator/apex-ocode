"""Minimal, allowlisted subprocess wrapper for ffmpeg -- this package's
own copy of the discipline verification/ffmpeg_runner.py established in
Release 0.9, not a shared import, same reasoning every sibling
ffmpeg_runner.py gives: each package that touches ffmpeg keeps its own
argv-construction self-contained per spec rule 18 ("keep media commands
allowlisted"). `subprocess.run` is always called with an argv list,
never `shell=True`.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .errors import CompositingError

DEFAULT_TIMEOUT_SECONDS = 60.0


def _require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if path is None:
        raise CompositingError(["'ffmpeg' is not on PATH -- Release 0.13 requires ffmpeg to be installed"])
    return path


def _run(argv: list[str], timeout_seconds: float) -> None:
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        raise CompositingError([f"command timed out after {timeout_seconds}s: {' '.join(argv)}"]) from exc
    if result.returncode != 0:
        raise CompositingError([f"command failed (exit {result.returncode}): {' '.join(argv)}", result.stderr.strip()])


def run_ffmpeg_composite(
    background_path: Path,
    foreground_path: Path,
    output_path: Path,
    mask_type: str,
    chroma_color: str | None = None,
    chroma_similarity: float = 0.3,
    chroma_blend: float = 0.1,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> None:
    """Overlays `foreground_path` on top of `background_path`.
    `mask_type="chromakey"` first keys out `chroma_color` from the
    foreground (ffmpeg's `colorkey` filter) before overlaying it, so
    only the non-keyed pixels show through to the background --
    `mask_type="none"` overlays the foreground opaquely with no keying.
    `overlay=shortest=1` bounds the output to the shorter of the two
    inputs, since a foreground/background pair from two different
    generations has no guarantee of matching duration."""
    if mask_type not in ("chromakey", "none"):
        raise CompositingError([f"run_ffmpeg_composite does not execute mask_type {mask_type!r}"])
    if mask_type == "chromakey" and not chroma_color:
        raise CompositingError(["mask_type is 'chromakey' but no chroma_color was given"])

    binary = _require_ffmpeg()
    argv = [binary, "-y", "-v", "error", "-i", str(background_path), "-i", str(foreground_path)]
    if mask_type == "chromakey":
        filter_complex = (
            f"[1:v]colorkey=color={chroma_color}:similarity={chroma_similarity}:blend={chroma_blend}[fg];"
            f"[0:v][fg]overlay=shortest=1[out]"
        )
    else:
        filter_complex = "[0:v][1:v]overlay=shortest=1[out]"
    argv += [
        "-filter_complex", filter_complex, "-map", "[out]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path),
    ]
    _run(argv, timeout_seconds)
