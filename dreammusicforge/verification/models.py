"""Typed domain model for Release 0.9 -- "objective technical report
generated from video files" (spec section 19's acceptance test for this
release).

Every numeric field here is measured from a real file via
verification/ffmpeg_runner.py, never asserted or fabricated -- see that
module's docstring for why ffmpeg/ffprobe, and this module's field
choices trace directly to spec section 9.1's "Technical checks" list
(duration, frame rate, resolution, codec, audio presence) plus section
19's Release 0.9 "Build" list (media inspection, frame extraction, seam
comparison, audio RMS, color shift, duration and frame-rate checks).

Same to_dict()/from_dict() convention as the rest of this repo's domain
models -- frozen dataclasses, not the JSON-Schema-in-a-dict pattern used
elsewhere in this repo's sibling dreammusicforge module.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MediaMetadata:
    duration_seconds: float
    frame_rate: float
    width: int
    height: int
    video_codec: str
    has_audio: bool
    audio_codec: str | None = None

    def to_dict(self) -> dict:
        return {
            "duration_seconds": self.duration_seconds,
            "frame_rate": self.frame_rate,
            "width": self.width,
            "height": self.height,
            "video_codec": self.video_codec,
            "has_audio": self.has_audio,
            "audio_codec": self.audio_codec,
        }

    @staticmethod
    def from_dict(data: dict) -> "MediaMetadata":
        return MediaMetadata(
            duration_seconds=float(data["duration_seconds"]),
            frame_rate=float(data["frame_rate"]),
            width=int(data["width"]),
            height=int(data["height"]),
            video_codec=data["video_codec"],
            has_audio=bool(data["has_audio"]),
            audio_codec=data.get("audio_codec"),
        )


@dataclass(frozen=True)
class DurationFrameRateCheck:
    expected_duration_seconds: float
    measured_duration_seconds: float
    expected_frame_rate: float
    measured_frame_rate: float
    duration_tolerance_seconds: float
    frame_rate_tolerance: float
    within_tolerance: bool

    def to_dict(self) -> dict:
        return {
            "expected_duration_seconds": self.expected_duration_seconds,
            "measured_duration_seconds": self.measured_duration_seconds,
            "expected_frame_rate": self.expected_frame_rate,
            "measured_frame_rate": self.measured_frame_rate,
            "duration_tolerance_seconds": self.duration_tolerance_seconds,
            "frame_rate_tolerance": self.frame_rate_tolerance,
            "within_tolerance": self.within_tolerance,
        }

    @staticmethod
    def from_dict(data: dict) -> "DurationFrameRateCheck":
        return DurationFrameRateCheck(
            expected_duration_seconds=float(data["expected_duration_seconds"]),
            measured_duration_seconds=float(data["measured_duration_seconds"]),
            expected_frame_rate=float(data["expected_frame_rate"]),
            measured_frame_rate=float(data["measured_frame_rate"]),
            duration_tolerance_seconds=float(data["duration_tolerance_seconds"]),
            frame_rate_tolerance=float(data["frame_rate_tolerance"]),
            within_tolerance=bool(data["within_tolerance"]),
        )


@dataclass(frozen=True)
class AudioRmsReport:
    rms_level_db: float
    peak_level_db: float
    silent: bool

    def to_dict(self) -> dict:
        return {"rms_level_db": self.rms_level_db, "peak_level_db": self.peak_level_db, "silent": self.silent}

    @staticmethod
    def from_dict(data: dict) -> "AudioRmsReport":
        return AudioRmsReport(rms_level_db=float(data["rms_level_db"]), peak_level_db=float(data["peak_level_db"]), silent=bool(data["silent"]))


@dataclass(frozen=True)
class SeamComparison:
    ssim_score: float
    similar: bool

    def to_dict(self) -> dict:
        return {"ssim_score": self.ssim_score, "similar": self.similar}

    @staticmethod
    def from_dict(data: dict) -> "SeamComparison":
        return SeamComparison(ssim_score=float(data["ssim_score"]), similar=bool(data["similar"]))


@dataclass(frozen=True)
class ColorShiftReport:
    delta_y: float
    delta_u: float
    delta_v: float
    shifted: bool

    def to_dict(self) -> dict:
        return {"delta_y": self.delta_y, "delta_u": self.delta_u, "delta_v": self.delta_v, "shifted": self.shifted}

    @staticmethod
    def from_dict(data: dict) -> "ColorShiftReport":
        return ColorShiftReport(delta_y=float(data["delta_y"]), delta_u=float(data["delta_u"]), delta_v=float(data["delta_v"]), shifted=bool(data["shifted"]))


@dataclass(frozen=True)
class TechnicalReport:
    candidate_id: str
    file: str
    media: MediaMetadata
    duration_frame_rate_check: DurationFrameRateCheck
    audio_rms: AudioRmsReport | None
    seam_comparison: SeamComparison | None
    color_shift: ColorShiftReport | None
    passed: bool
    failures: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "file": self.file,
            "media": self.media.to_dict(),
            "duration_frame_rate_check": self.duration_frame_rate_check.to_dict(),
            "audio_rms": self.audio_rms.to_dict() if self.audio_rms is not None else None,
            "seam_comparison": self.seam_comparison.to_dict() if self.seam_comparison is not None else None,
            "color_shift": self.color_shift.to_dict() if self.color_shift is not None else None,
            "passed": self.passed,
            "failures": list(self.failures),
        }

    @staticmethod
    def from_dict(data: dict) -> "TechnicalReport":
        audio_rms = data.get("audio_rms")
        seam = data.get("seam_comparison")
        color_shift = data.get("color_shift")
        return TechnicalReport(
            candidate_id=data["candidate_id"],
            file=data["file"],
            media=MediaMetadata.from_dict(data["media"]),
            duration_frame_rate_check=DurationFrameRateCheck.from_dict(data["duration_frame_rate_check"]),
            audio_rms=AudioRmsReport.from_dict(audio_rms) if audio_rms is not None else None,
            seam_comparison=SeamComparison.from_dict(seam) if seam is not None else None,
            color_shift=ColorShiftReport.from_dict(color_shift) if color_shift is not None else None,
            passed=bool(data["passed"]),
            failures=tuple(data.get("failures", [])),
        )
