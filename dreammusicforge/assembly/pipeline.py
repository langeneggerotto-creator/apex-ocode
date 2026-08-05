"""normalize_clip()/concatenate_clips()/replace_audio(): the "clip
normalization," "chronological assembly," and "master-audio
replacement" deliverables (spec section 19), each a thin, typed
wrapper over assembly/ffmpeg_runner.py's argv-construction.
"""
from __future__ import annotations

from pathlib import Path

from .ffmpeg_runner import run_ffmpeg_concat, run_ffmpeg_normalize, run_ffmpeg_replace_audio


def normalize_clip(input_path: Path, output_path: Path, width: int, height: int, frame_rate: float) -> Path:
    run_ffmpeg_normalize(input_path, output_path, width, height, frame_rate)
    return output_path


def concatenate_clips(clip_paths: tuple[Path, ...], output_path: Path) -> Path:
    run_ffmpeg_concat(clip_paths, output_path)
    return output_path


def replace_audio(video_only_path: Path, audio_path: Path, output_path: Path, duration_seconds: float) -> Path:
    run_ffmpeg_replace_audio(video_only_path, audio_path, output_path, duration_seconds)
    return output_path
