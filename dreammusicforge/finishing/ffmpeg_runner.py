"""Minimal, allowlisted subprocess wrapper for ffmpeg -- this package's
own copy of the discipline verification/ffmpeg_runner.py established in
Release 0.9, not a shared import, same reasoning every sibling
ffmpeg_runner.py gives: each package that touches ffmpeg keeps its own
argv-construction self-contained per spec rule 18 ("keep media commands
allowlisted"). `subprocess.run` is always called with an argv list,
never `shell=True`.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .errors import FinishingError

DEFAULT_TIMEOUT_SECONDS = 60.0


def _require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if path is None:
        raise FinishingError(["'ffmpeg' is not on PATH -- Release 0.14 requires ffmpeg to be installed"])
    return path


def _run(argv: list[str], timeout_seconds: float) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        raise FinishingError([f"command timed out after {timeout_seconds}s: {' '.join(argv)}"]) from exc
    if result.returncode != 0:
        raise FinishingError([f"command failed (exit {result.returncode}): {' '.join(argv)}", result.stderr.strip()])
    return result


def run_ffmpeg_measure_loudness(input_path: Path, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Runs ffmpeg's `loudnorm` filter in its single-pass measurement
    mode and returns the real EBU R128 stats it reports (as a parsed
    dict with keys like `input_i`, `input_tp`, `input_lra`) -- not an
    estimate. `loudnorm` prints this as a JSON block to stderr at the
    default (info) log level, so this call deliberately does not pass
    `-v error` the way every other wrapper in this repository does."""
    binary = _require_ffmpeg()
    argv = [binary, "-i", str(input_path), "-af", "loudnorm=print_format=json", "-f", "null", "-"]
    result = _run(argv, timeout_seconds)

    stderr = result.stderr
    start, end = stderr.find("{"), stderr.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise FinishingError([f"could not find loudnorm JSON stats in ffmpeg output: {stderr[-500:]}"])
    try:
        return json.loads(stderr[start:end + 1])
    except json.JSONDecodeError as exc:
        raise FinishingError([f"could not parse loudnorm JSON stats: {exc}"]) from exc


def run_ffmpeg_normalize_loudness(
    input_path: Path,
    output_path: Path,
    target_lufs: float,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> None:
    """Single-pass loudness normalization to target_lufs integrated
    loudness via ffmpeg's `loudnorm` filter. Single-pass (rather than
    the more precise two-pass measure-then-normalize sequence) trades
    some accuracy for one ffmpeg invocation instead of two -- acceptable
    here since this release's own acceptance test only requires the
    result to move measurably closer to the target, not to hit it
    exactly (see finishing/builder.py)."""
    binary = _require_ffmpeg()
    argv = [
        binary, "-y", "-v", "error", "-i", str(input_path),
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
        "-c:v", "copy", str(output_path),
    ]
    _run(argv, timeout_seconds)


def run_ffmpeg_color_adjust(
    input_path: Path,
    output_path: Path,
    brightness: float,
    contrast: float,
    saturation: float,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> None:
    """Applies a brightness/contrast/saturation adjustment via ffmpeg's
    `eq` filter -- real pixel-level grading, not a metadata tag."""
    binary = _require_ffmpeg()
    argv = [
        binary, "-y", "-v", "error", "-i", str(input_path),
        "-vf", f"eq=brightness={brightness}:contrast={contrast}:saturation={saturation}",
        "-c:a", "copy", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path),
    ]
    _run(argv, timeout_seconds)
