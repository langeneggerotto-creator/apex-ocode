"""Minimal, allowlisted subprocess wrapper for ffmpeg -- this package's
own copy of the discipline verification/ffmpeg_runner.py established in
Release 0.9, not a shared import, same reasoning assembly/ffmpeg_runner.py
gives: each package that touches ffmpeg keeps its own argv-construction
self-contained per spec rule 18 ("keep media commands allowlisted").

The one function here builds a complete, fixed-shape argv from typed
parameters (Path, float) -- no raw command string or open-ended argument
list from a caller, and `subprocess.run` is always called with an argv
list, never `shell=True`.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .errors import LipSyncError

DEFAULT_TIMEOUT_SECONDS = 30.0


def _require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if path is None:
        raise LipSyncError(["'ffmpeg' is not on PATH -- Release 0.12 requires ffmpeg to be installed"])
    return path


def run_ffmpeg_extract_audio_window(
    source_file: Path,
    start_seconds: float,
    end_seconds: float,
    output_path: Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> None:
    """Extracts one continuous audio window [start_seconds, end_seconds)
    from source_file -- used to pull the exact slice of the canonical
    MasterSong a given shot's lip-sync needs, so a real lip-sync engine
    receives a concrete, traceable audio file rather than a time range
    it would have to re-derive itself."""
    binary = shutil.which("ffmpeg")
    if binary is None:
        raise LipSyncError(["'ffmpeg' is not on PATH -- Release 0.12 requires ffmpeg to be installed"])

    duration = end_seconds - start_seconds
    argv = [
        binary, "-y", "-v", "error", "-ss", f"{start_seconds}", "-i", str(source_file),
        "-t", f"{duration}", "-ac", "2", str(output_path),
    ]
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        raise LipSyncError([f"command timed out after {timeout_seconds}s: {' '.join(argv)}"]) from exc
    if result.returncode != 0:
        raise LipSyncError([f"command failed (exit {result.returncode}): {' '.join(argv)}", result.stderr.strip()])
