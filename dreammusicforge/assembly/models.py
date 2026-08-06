"""Typed domain model for Release 0.11 -- "accepted shots assemble into
one video with uninterrupted song" (spec section 19's acceptance test
for this release).

TRANSITION_TYPES matches spec section 8.6's ten named transition
contracts verbatim (hard cut, dissolve, dip to black, foreground wipe,
motion match, graphic match, color bridge, light flash, blur
transition, beat cut). `Transition`'s fields match section 8.6's
"every transition must declare" list exactly (source shot, destination
shot, duration, musical anchor, visual bridge, semantic purpose). This
release actually executes only `hard_cut` -- see `assembly/concat.py`'s
module docstring for why: it's the one transition type that needs no
compositing, and it's also the exact technique this session's own real
reference video used to move between deliberately distinct scenes (see
README.md's "Design choices" section for the grounding).

`dissolve` was added to EXECUTABLE_TRANSITION_TYPES after reviewing a
real professionally-produced reference video: it relies on more than
hard cuts to move between chapters, and a crossfade (ffmpeg's `xfade`
filter) is the one other transition in spec section 8.6's list that
needs no additional compositing input beyond the two adjacent clips
themselves -- unlike foreground_wipe/motion_match/graphic_match/etc.,
which need extra assets or motion analysis this repository doesn't
have yet. The remaining eight transition types still fail closed.

`ExportManifest` is this release's own addition -- the spec names
"export manifest" as a Build deliverable (section 19) but gives no
worked YAML example the way sections 6.1-6.11 do for other entities.
Its shape follows this repository's established evidence pattern: every
clip that went into the final file is traceable back to the Candidate
(and its real sha256 hash, Release 0.8) that produced it.

Same to_dict()/from_dict() convention as the rest of this repo's domain
models -- frozen dataclasses, not the JSON-Schema-in-a-dict pattern used
elsewhere in this repo's sibling dreammusicforge module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

TRANSITION_TYPES = (
    "hard_cut", "dissolve", "dip_to_black", "foreground_wipe", "motion_match",
    "graphic_match", "color_bridge", "light_flash", "blur_transition", "beat_cut",
)

EXECUTABLE_TRANSITION_TYPES = ("hard_cut", "dissolve")


@dataclass(frozen=True)
class Transition:
    source_shot_id: str
    destination_shot_id: str
    transition_type: str
    duration_seconds: float
    musical_anchor: str
    visual_bridge: str
    semantic_purpose: str

    def to_dict(self) -> dict:
        return {
            "source_shot_id": self.source_shot_id,
            "destination_shot_id": self.destination_shot_id,
            "transition_type": self.transition_type,
            "duration_seconds": self.duration_seconds,
            "musical_anchor": self.musical_anchor,
            "visual_bridge": self.visual_bridge,
            "semantic_purpose": self.semantic_purpose,
        }

    @staticmethod
    def from_dict(data: dict) -> "Transition":
        return Transition(
            source_shot_id=data["source_shot_id"],
            destination_shot_id=data["destination_shot_id"],
            transition_type=data["transition_type"],
            duration_seconds=float(data["duration_seconds"]),
            musical_anchor=data["musical_anchor"],
            visual_bridge=data["visual_bridge"],
            semantic_purpose=data["semantic_purpose"],
        )


@dataclass(frozen=True)
class AssembledClip:
    candidate_id: str
    shot_id: str
    source_hash: str
    start_seconds_in_final: float
    normalized_duration_seconds: float

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "shot_id": self.shot_id,
            "source_hash": self.source_hash,
            "start_seconds_in_final": self.start_seconds_in_final,
            "normalized_duration_seconds": self.normalized_duration_seconds,
        }

    @staticmethod
    def from_dict(data: dict) -> "AssembledClip":
        return AssembledClip(
            candidate_id=data["candidate_id"],
            shot_id=data["shot_id"],
            source_hash=data["source_hash"],
            start_seconds_in_final=float(data["start_seconds_in_final"]),
            normalized_duration_seconds=float(data["normalized_duration_seconds"]),
        )


@dataclass(frozen=True)
class ExportManifest:
    id: str
    master_song_id: str
    master_song_hash: str
    output_file: str
    output_hash: str
    total_duration_seconds: float
    created_at: str
    clips: tuple[AssembledClip, ...] = field(default_factory=tuple)
    transitions: tuple[Transition, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "master_song_id": self.master_song_id,
            "master_song_hash": self.master_song_hash,
            "output_file": self.output_file,
            "output_hash": self.output_hash,
            "total_duration_seconds": self.total_duration_seconds,
            "created_at": self.created_at,
            "clips": [clip.to_dict() for clip in self.clips],
            "transitions": [transition.to_dict() for transition in self.transitions],
        }

    @staticmethod
    def from_dict(data: dict) -> "ExportManifest":
        return ExportManifest(
            id=data["id"],
            master_song_id=data["master_song_id"],
            master_song_hash=data["master_song_hash"],
            output_file=data["output_file"],
            output_hash=data["output_hash"],
            total_duration_seconds=float(data["total_duration_seconds"]),
            created_at=data["created_at"],
            clips=tuple(AssembledClip.from_dict(item) for item in data.get("clips", [])),
            transitions=tuple(Transition.from_dict(item) for item in data.get("transitions", [])),
        )
