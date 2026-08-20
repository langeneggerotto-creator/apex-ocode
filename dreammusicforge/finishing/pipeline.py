"""measure_loudness()/normalize_loudness()/adjust_color(): thin, typed
wrappers over finishing/ffmpeg_runner.py's argv-construction.
"""
from __future__ import annotations

from pathlib import Path

from .ffmpeg_runner import run_ffmpeg_color_adjust, run_ffmpeg_measure_loudness, run_ffmpeg_normalize_loudness
from .models import ColorAdjustment, LoudnessReport


def measure_loudness(input_path: Path) -> LoudnessReport:
    stats = run_ffmpeg_measure_loudness(input_path)
    return LoudnessReport(
        integrated_lufs=float(stats["input_i"]),
        true_peak_dbfs=float(stats["input_tp"]),
        loudness_range_lu=float(stats["input_lra"]),
    )


def normalize_loudness(input_path: Path, output_path: Path, target_lufs: float) -> Path:
    run_ffmpeg_normalize_loudness(input_path, output_path, target_lufs)
    return output_path


def adjust_color(input_path: Path, output_path: Path, color_adjustment: ColorAdjustment) -> Path:
    run_ffmpeg_color_adjust(
        input_path, output_path, color_adjustment.brightness, color_adjustment.contrast, color_adjustment.saturation,
    )
    return output_path
