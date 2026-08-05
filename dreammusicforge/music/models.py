"""Typed domain model for Release 0.2 -- "one song can become a canonical
timeline" (spec section 19's acceptance test for this release).

Same convention as core/models.py: plain frozen dataclasses with
to_dict()/from_dict() round-tripping, not the JSON-Schema-in-a-dict
pattern used elsewhere in this repo's sibling dreammusicforge module.
music/schema.py is the structural contract raw dict input is checked
against before being parsed into these types; from_dict() here assumes
that check already ran, same discipline as core.models.Project.from_dict.

MasterSong.bpm and .time_signature are declared metadata (spec section
6.2's master_song fields) -- supplied by a human or an earlier stage, not
derived by this release from the audio itself. See music/beats.py and
music/wav_inspector.py for the stated boundary on what audio analysis
this release does and does not perform.
"""
from __future__ import annotations

from dataclasses import dataclass, field

SECTION_TYPES = {
    "intro", "verse", "pre_chorus", "chorus", "bridge", "outro", "instrumental", "hook",
}


@dataclass(frozen=True)
class Beat:
    index: int
    time: float
    bar: int
    beat_in_bar: int

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "time": self.time,
            "bar": self.bar,
            "beat_in_bar": self.beat_in_bar,
        }

    @staticmethod
    def from_dict(data: dict) -> "Beat":
        return Beat(
            index=int(data["index"]),
            time=float(data["time"]),
            bar=int(data["bar"]),
            beat_in_bar=int(data["beat_in_bar"]),
        )


@dataclass(frozen=True)
class Section:
    id: str
    type: str
    start_seconds: float
    end_seconds: float
    label: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "label": self.label,
        }

    @staticmethod
    def from_dict(data: dict) -> "Section":
        return Section(
            id=data["id"],
            type=data["type"],
            start_seconds=float(data["start_seconds"]),
            end_seconds=float(data["end_seconds"]),
            label=data.get("label"),
        )


@dataclass(frozen=True)
class LyricLine:
    id: str
    start_seconds: float
    end_seconds: float
    text: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "text": self.text,
        }

    @staticmethod
    def from_dict(data: dict) -> "LyricLine":
        return LyricLine(
            id=data["id"],
            start_seconds=float(data["start_seconds"]),
            end_seconds=float(data["end_seconds"]),
            text=data["text"],
        )


@dataclass(frozen=True)
class MasterSong:
    id: str
    source_file: str
    duration_seconds: float
    sample_rate: int
    channels: int
    bpm: float
    time_signature: str
    hash: str
    stems: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_file": self.source_file,
            "duration_seconds": self.duration_seconds,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "bpm": self.bpm,
            "time_signature": self.time_signature,
            "hash": self.hash,
            "stems": dict(self.stems),
        }

    @staticmethod
    def from_dict(data: dict) -> "MasterSong":
        return MasterSong(
            id=data["id"],
            source_file=data["source_file"],
            duration_seconds=float(data["duration_seconds"]),
            sample_rate=int(data["sample_rate"]),
            channels=int(data["channels"]),
            bpm=float(data["bpm"]),
            time_signature=data["time_signature"],
            hash=data["hash"],
            stems=dict(data.get("stems", {})),
        )


@dataclass(frozen=True)
class Timeline:
    """The canonical timeline for one MasterSong: its sections, beat grid,
    and lyric lines, all anchored to the same seconds axis as the master
    audio (per the spec's Law 2 -- music is the master clock)."""

    master_song_id: str
    sections: tuple[Section, ...] = field(default_factory=tuple)
    beats: tuple[Beat, ...] = field(default_factory=tuple)
    lyric_lines: tuple[LyricLine, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "master_song_id": self.master_song_id,
            "sections": [section.to_dict() for section in self.sections],
            "beats": [beat.to_dict() for beat in self.beats],
            "lyric_lines": [line.to_dict() for line in self.lyric_lines],
        }

    @staticmethod
    def from_dict(data: dict) -> "Timeline":
        return Timeline(
            master_song_id=data["master_song_id"],
            sections=tuple(Section.from_dict(item) for item in data.get("sections", [])),
            beats=tuple(Beat.from_dict(item) for item in data.get("beats", [])),
            lyric_lines=tuple(LyricLine.from_dict(item) for item in data.get("lyric_lines", [])),
        )
