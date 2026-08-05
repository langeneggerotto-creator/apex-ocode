"""Minimal, allowlisted subprocess wrapper for ffmpeg -- this package's
own copy of the discipline verification/ffmpeg_runner.py established in
Release 0.9, not a shared import, because these two packages invoke
ffmpeg for entirely different purposes (probing/analysis there,
encoding/muxing here) and each keeps its own argv-construction
self-contained per spec rule 18 ("keep media commands allowlisted").

Every function here builds its own complete, fixed-shape argv from
typed parameters (Path, float, int) -- no function accepts a raw
command string or an open-ended argument list from a caller, and
`subprocess.run` is always called with an argv list, never
`shell=True`.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .errors import AssemblyError

DEFAULT_TIMEOUT_SECONDS = 60.0


def _require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if path is None:
        raise AssemblyError(["'ffmpeg' is not on PATH -- Release 0.11 requires ffmpeg to be installed"])
    return path


def _run(argv: list[str], timeout_seconds: float) -> None:
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        raise AssemblyError([f"command timed out after {timeout_seconds}s: {' '.join(argv)}"]) from exc
    if result.returncode != 0:
        raise AssemblyError([f"command failed (exit {result.returncode}): {' '.join(argv)}", result.stderr.strip()])


def run_ffmpeg_normalize(
    input_path: Path,
    output_path: Path,
    width: int,
    height: int,
    frame_rate: float,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> None:
    """Re-scales and re-times a clip to a target resolution/frame rate,
    resetting its timestamps and dropping its audio entirely -- the
    final assembled file's audio always comes from replace_audio()
    pulling the canonical MasterSong (spec Law 3.9), never from
    per-clip audio.

    `setsar=1` forces square pixels explicitly: two source clips with
    different native aspect ratios (e.g. real Kling output at 480x854
    vs 720x1280) can scale to identical pixel dimensions but still carry
    slightly different sample-aspect-ratio metadata, which makes
    ffmpeg's concat filter refuse to join them ("Input link parameters
    do not match the corresponding output link parameters") even though
    the frames themselves are the same size -- found by running this
    function against two differently-sourced real clips, not by a unit
    test in isolation."""
    binary = _require_ffmpeg()
    argv = [
        binary, "-y", "-v", "error", "-i", str(input_path),
        "-vf", f"scale={width}:{height},setsar=1,fps={frame_rate},setpts=PTS-STARTPTS",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path),
    ]
    _run(argv, timeout_seconds)


def run_ffmpeg_concat(clip_paths: tuple[Path, ...], output_path: Path, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> None:
    """Concatenates already-normalized (same resolution/frame rate,
    video-only) clips via filter_complex concat -- not stream-copy
    concat, which is exactly the bug this repository's pre-spec
    `runtime.py`/`schemas/assembly_package.py` work (in the sibling
    `agentic-twin` repository) root-caused a real "no audio in the
    stitched video" failure to: stream-copy passes each clip's original
    timestamps through unchanged, and independently-generated clips
    don't share a timestamp origin. Every input here was already
    timestamp-reset by run_ffmpeg_normalize()'s setpts filter, and this
    filter_complex pass re-decodes and re-encodes rather than copying,
    so the same discontinuity can't recur."""
    binary = _require_ffmpeg()
    argv = [binary, "-y", "-v", "error"]
    for path in clip_paths:
        argv += ["-i", str(path)]
    stream_labels = "".join(f"[{index}:v]" for index in range(len(clip_paths)))
    filter_complex = f"{stream_labels}concat=n={len(clip_paths)}:v=1:a=0[outv]"
    argv += ["-filter_complex", filter_complex, "-map", "[outv]", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path)]
    _run(argv, timeout_seconds)


def run_ffmpeg_replace_audio(
    video_only_path: Path,
    audio_path: Path,
    output_path: Path,
    duration_seconds: float,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> None:
    """Muxes the concatenated video-only stream with the canonical
    MasterSong audio (Law 3.9: "master audio remains external" --
    provider-generated audio must not replace the canonical song), not
    the other way around. `-shortest` bounds the output to
    duration_seconds so a master song longer than the assembled video
    doesn't trail on past the last frame."""
    binary = _require_ffmpeg()
    argv = [
        binary, "-y", "-v", "error", "-i", str(video_only_path), "-i", str(audio_path),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-t", f"{duration_seconds}", "-movflags", "+faststart", str(output_path),
    ]
    _run(argv, timeout_seconds)
