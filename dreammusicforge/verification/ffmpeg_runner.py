"""Minimal, allowlisted subprocess wrapper for ffmpeg/ffprobe -- the one
place this repository invokes an external binary rather than relying on
stdlib alone.

Why here, and why not stdlib: Release 0.2's `music/wav_inspector.py`
reads WAV files with stdlib `wave` because PCM WAV headers are trivial
to parse by hand -- no decoding needed. There is no equivalent for the
H.264-encoded video and AAC-encoded audio this release has to inspect;
Python's stdlib has no video or compressed-audio codec at all, and
writing one is not a reasonable scope for a single release (or several).
The alternatives were: (a) a third-party Python package (a decode
library, or bindings to one), or (b) shelling out to ffmpeg/ffprobe,
confirmed present in this environment and already proven, in the
sibling `agentic-twin` repository's own DreamMusicForge work, for
exactly this kind of real diagnostic (`volumedetect`/`astats`/
`silencedetect`). This module takes (b): no new Python dependency, and
the actual media-analysis logic (SSIM, RMS, YUV averages) is delegated
to a tool built for it instead of reimplemented.

Spec section 22's rule 18 says "keep media commands allowlisted." The
allowlist here is structural, not a runtime check against a list of
permitted strings: every function below builds its own complete,
fixed-shape argv internally from typed parameters (`Path`, `float`) --
there is no function anywhere in this package that accepts a raw
command string or an open-ended list of ffmpeg arguments from a caller.
`subprocess.run` is always called with an argv list, never `shell=True`.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .errors import FfmpegNotAvailableError, FfmpegRunError

DEFAULT_TIMEOUT_SECONDS = 30.0

_SSIM_ALL_PATTERN = re.compile(r"SSIM .*?All:([\d.]+)")
_ASTATS_PEAK_PATTERN = re.compile(r"Peak level dB:\s*(-?[\d.]+|-inf)")
_ASTATS_RMS_PATTERN = re.compile(r"RMS level dB:\s*(-?[\d.]+|-inf)")
_SIGNALSTATS_PATTERN = re.compile(r"lavfi\.signalstats\.(YAVG|UAVG|VAVG)=([\d.]+)")


def _require_binary(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise FfmpegNotAvailableError(name)
    return path


def _run(argv: list[str], timeout_seconds: float) -> str:
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        raise FfmpegRunError([f"command timed out after {timeout_seconds}s: {' '.join(argv)}"]) from exc
    if result.returncode != 0:
        raise FfmpegRunError([f"command failed (exit {result.returncode}): {' '.join(argv)}", result.stderr.strip()])
    return result.stdout + result.stderr


def _parse_db_value(raw: str) -> float:
    return float("-inf") if raw == "-inf" else float(raw)


def run_ffprobe_json(file_path: Path, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> dict:
    binary = _require_binary("ffprobe")
    argv = [binary, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(file_path)]
    output = _run(argv, timeout_seconds)
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise FfmpegRunError([f"ffprobe returned non-JSON output for {file_path}: {exc}"]) from exc


def run_ffmpeg_extract_frame(file_path: Path, timestamp_seconds: float, output_path: Path, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> None:
    binary = _require_binary("ffmpeg")
    argv = [
        binary, "-y", "-v", "error", "-ss", f"{timestamp_seconds}", "-i", str(file_path),
        "-frames:v", "1", str(output_path),
    ]
    _run(argv, timeout_seconds)
    if not output_path.is_file():
        raise FfmpegRunError([f"ffmpeg did not produce an output frame at {output_path}"])


def run_ffmpeg_ssim(frame_a: Path, frame_b: Path, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> float:
    """Returns the aggregate SSIM score ("All:") in [0, 1]. ffmpeg's
    ssim filter labels per-channel scores R/G/B or Y/U/V depending on
    the input pixel format (PNG frames from extract_frame() are RGB,
    not YUV) -- only the aggregate is stable across both, so that's all
    this wrapper parses."""
    binary = _require_binary("ffmpeg")
    argv = [
        binary, "-v", "info", "-hide_banner", "-i", str(frame_a), "-i", str(frame_b),
        "-filter_complex", "[0:v][1:v]ssim", "-f", "null", "-",
    ]
    output = _run(argv, timeout_seconds)
    match = _SSIM_ALL_PATTERN.search(output)
    if not match:
        raise FfmpegRunError([f"could not parse SSIM output comparing {frame_a} and {frame_b}"])
    return float(match.group(1))


def run_ffmpeg_astats(file_path: Path, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, float]:
    binary = _require_binary("ffmpeg")
    argv = [binary, "-v", "info", "-hide_banner", "-i", str(file_path), "-af", "astats", "-f", "null", "-"]
    output = _run(argv, timeout_seconds)

    peak_matches = _ASTATS_PEAK_PATTERN.findall(output)
    rms_matches = _ASTATS_RMS_PATTERN.findall(output)
    if not peak_matches or not rms_matches:
        raise FfmpegRunError([f"could not parse astats output for {file_path}"])
    return {"peak_level_db": _parse_db_value(peak_matches[-1]), "rms_level_db": _parse_db_value(rms_matches[-1])}


def run_ffmpeg_signalstats(frame_path: Path, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, float]:
    binary = _require_binary("ffmpeg")
    argv = [
        binary, "-v", "info", "-hide_banner", "-i", str(frame_path), "-vf", "signalstats,metadata=print",
        "-frames:v", "1", "-f", "null", "-",
    ]
    output = _run(argv, timeout_seconds)
    values: dict[str, float] = {}
    for key, value in _SIGNALSTATS_PATTERN.findall(output):
        values.setdefault(key.lower(), float(value))
    if not {"yavg", "uavg", "vavg"} <= values.keys():
        raise FfmpegRunError([f"could not parse signalstats output for {frame_path}"])
    return values
