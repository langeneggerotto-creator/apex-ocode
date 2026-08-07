from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TransitionType(str, Enum):
    CUT = "CUT"
    DISSOLVE = "DISSOLVE"
    FOREGROUND_WIPE = "FOREGROUND_WIPE"
    MATCH_ACTION = "MATCH_ACTION"
    LIGHT_FLASH = "LIGHT_FLASH"


@dataclass(frozen=True)
class AcceptedAsset:
    candidate_id: str
    file_name: str
    sha256: str
    start_seconds: float
    end_seconds: float
    width: int
    height: int
    fps: float
    has_audio: bool = True

    def validate(self) -> None:
        if not self.candidate_id.strip() or not self.file_name.strip() or not self.sha256.strip():
            raise ValueError("asset identifiers are required")
        if self.start_seconds < 0 or self.end_seconds <= self.start_seconds:
            raise ValueError("asset timeline interval is invalid")
        if self.width <= 0 or self.height <= 0 or self.fps <= 0:
            raise ValueError("asset dimensions and fps must be positive")


@dataclass(frozen=True)
class TransitionContract:
    source_candidate_id: str
    destination_candidate_id: str
    transition_type: TransitionType
    duration_seconds: float = 0.0
    musical_anchor_seconds: float | None = None
    semantic_purpose: str = "continuity"

    def validate(self) -> None:
        if not self.source_candidate_id.strip() or not self.destination_candidate_id.strip():
            raise ValueError("transition candidate ids are required")
        if self.duration_seconds < 0:
            raise ValueError("transition duration cannot be negative")
        if self.transition_type is TransitionType.CUT and self.duration_seconds != 0:
            raise ValueError("hard cut duration must be zero")


@dataclass(frozen=True)
class MasterAudioContract:
    file_name: str
    sha256: str
    duration_seconds: float
    start_offset_seconds: float = 0.0

    def validate(self) -> None:
        if not self.file_name.strip() or not self.sha256.strip():
            raise ValueError("master audio identifiers are required")
        if self.duration_seconds <= 0 or self.start_offset_seconds < 0:
            raise ValueError("master audio timing is invalid")


@dataclass(frozen=True)
class NormalizationTarget:
    width: int
    height: int
    fps: float
    video_codec: str = "libx264"
    pixel_format: str = "yuv420p"

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0 or self.fps <= 0:
            raise ValueError("normalization dimensions and fps must be positive")
        if not self.video_codec.strip() or not self.pixel_format.strip():
            raise ValueError("normalization codec and pixel format are required")


@dataclass(frozen=True)
class SeamRecord:
    source_candidate_id: str
    destination_candidate_id: str
    source_end_seconds: float
    destination_start_seconds: float
    transition_type: TransitionType
    requires_seam_verification: bool


@dataclass(frozen=True)
class AssemblyManifest:
    manifest_id: str
    assets: tuple[AcceptedAsset, ...]
    transitions: tuple[TransitionContract, ...]
    master_audio: MasterAudioContract
    normalization: NormalizationTarget
    seams: tuple[SeamRecord, ...]
    mute_provider_audio: bool
    output_file_name: str

    def validate(self) -> None:
        if not self.manifest_id.strip() or not self.output_file_name.strip():
            raise ValueError("manifest_id and output_file_name are required")
        if not self.assets:
            raise ValueError("assembly requires at least one accepted asset")
        for asset in self.assets:
            asset.validate()
        for transition in self.transitions:
            transition.validate()
        self.master_audio.validate()
        self.normalization.validate()
