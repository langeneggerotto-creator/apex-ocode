"""Typed domain model for Release 0.14 -- Color and Audio Finishing.

Not verified against the original spec's own section text for this
release (only the release name survived this session's context
compaction, same gap as Releases 0.12/0.13). `-14.0` LUFS as the
default `target_lufs` is an industry-standard streaming-platform
loudness target (commonly cited for Spotify/YouTube), not a number
taken from the original spec text, which this session no longer has
access to -- see finishing/builder.py's docstring.

LoudnessReport carries real, ffmpeg-measured EBU R128 numbers (via the
`loudnorm` filter's own single-pass measurement mode) -- integrated
loudness, true peak, and loudness range -- not estimates.
ColorAdjustment is a simple brightness/contrast/saturation triple
(ffmpeg's `eq` filter parameters); `is_identity()` reports whether it's
a no-op, so finishing/builder.py can skip a needless re-encode.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoudnessReport:
    integrated_lufs: float
    true_peak_dbfs: float
    loudness_range_lu: float

    def to_dict(self) -> dict:
        return {
            "integrated_lufs": self.integrated_lufs,
            "true_peak_dbfs": self.true_peak_dbfs,
            "loudness_range_lu": self.loudness_range_lu,
        }

    @staticmethod
    def from_dict(data: dict) -> "LoudnessReport":
        return LoudnessReport(
            integrated_lufs=float(data["integrated_lufs"]),
            true_peak_dbfs=float(data["true_peak_dbfs"]),
            loudness_range_lu=float(data["loudness_range_lu"]),
        )


@dataclass(frozen=True)
class ColorAdjustment:
    brightness: float = 0.0
    contrast: float = 1.0
    saturation: float = 1.0

    def is_identity(self) -> bool:
        return self.brightness == 0.0 and self.contrast == 1.0 and self.saturation == 1.0

    def to_dict(self) -> dict:
        return {"brightness": self.brightness, "contrast": self.contrast, "saturation": self.saturation}

    @staticmethod
    def from_dict(data: dict) -> "ColorAdjustment":
        return ColorAdjustment(
            brightness=float(data.get("brightness", 0.0)),
            contrast=float(data.get("contrast", 1.0)),
            saturation=float(data.get("saturation", 1.0)),
        )


@dataclass(frozen=True)
class FinishingResult:
    id: str
    source_file: str
    output_file: str
    output_hash: str
    target_lufs: float
    measured_loudness: LoudnessReport
    color_adjustment: ColorAdjustment
    duration_seconds: float

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_file": self.source_file,
            "output_file": self.output_file,
            "output_hash": self.output_hash,
            "target_lufs": self.target_lufs,
            "measured_loudness": self.measured_loudness.to_dict(),
            "color_adjustment": self.color_adjustment.to_dict(),
            "duration_seconds": self.duration_seconds,
        }

    @staticmethod
    def from_dict(data: dict) -> "FinishingResult":
        return FinishingResult(
            id=data["id"],
            source_file=data["source_file"],
            output_file=data["output_file"],
            output_hash=data["output_hash"],
            target_lufs=float(data["target_lufs"]),
            measured_loudness=LoudnessReport.from_dict(data["measured_loudness"]),
            color_adjustment=ColorAdjustment.from_dict(data["color_adjustment"]),
            duration_seconds=float(data["duration_seconds"]),
        )
