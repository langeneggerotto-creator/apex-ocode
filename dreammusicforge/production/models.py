"""Typed domain model for Release 0.4 -- "project compiles into an
ordered production graph" (spec section 19's acceptance test for this
release).

Field shapes follow spec section 6.7 (semantic_event) and 6.8 (shot)
example YAML, with two deliberate departures stated here rather than
left implicit:

- `Shot` in this release carries only `timing`, `purpose`, `requirements`,
  `continuity`, and `acceptance` -- NOT `renderer_risk`, `slice_strategy`,
  `slices`, or `editing`. Section 6.8's worked example shows all of those
  on one `shot` object, but the pipeline diagram (spec section 2) and
  section 4.5 both place renderer-risk classification and slice-strategy
  selection at the Video Slicer stage, which comes *after* Production
  Graph compilation. Producing them here would mean claiming a later
  release's integration -- see "What Release 0.4 deliberately does not
  include" in the README.
- `Shot.continuity` (`inherited_state`/`permitted_mutations`/
  `destination_state`) is this release's own structure, not copied from
  section 6.8's YAML (which doesn't show a continuity block). It exists
  to satisfy Law 3.5's explicit requirement ("every shot must declare:
  inherited state; permitted mutations; expected destination state;
  continuity requirements; acceptance thresholds") and mirrors the
  source_state_id/destination_state_id state-chaining this same
  repository's pre-spec `runtime.py` already validates for exactly this
  purpose.

Same to_dict()/from_dict() convention as core/models.py's Project,
music/models.py's MasterSong, and genome/models.py's Performer -- frozen
dataclasses, not the JSON-Schema-in-a-dict pattern used elsewhere in
this repo's sibling dreammusicforge module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..genome.models import CameraLanguage, ColorLanguage


@dataclass(frozen=True)
class SemanticEvent:
    id: str
    start_seconds: float
    end_seconds: float
    meaning: str
    transformation_from: str
    transformation_to: str
    intended_viewer_inference: tuple[str, ...] = field(default_factory=tuple)
    required_visible_evidence: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "meaning": self.meaning,
            "transformation_from": self.transformation_from,
            "transformation_to": self.transformation_to,
            "intended_viewer_inference": list(self.intended_viewer_inference),
            "required_visible_evidence": list(self.required_visible_evidence),
        }

    @staticmethod
    def from_dict(data: dict) -> "SemanticEvent":
        return SemanticEvent(
            id=data["id"],
            start_seconds=float(data["start_seconds"]),
            end_seconds=float(data["end_seconds"]),
            meaning=data["meaning"],
            transformation_from=data["transformation_from"],
            transformation_to=data["transformation_to"],
            intended_viewer_inference=tuple(data.get("intended_viewer_inference", [])),
            required_visible_evidence=tuple(data.get("required_visible_evidence", [])),
        )


@dataclass(frozen=True)
class Sequence:
    """camera_language/color_language are optional per-sequence
    overrides of the FilmGenome's film-wide defaults -- added after
    reviewing a real professionally-produced reference video in this
    session: a multi-chapter piece visibly changes its camera vocabulary
    and color grading at chapter (sequence) boundaries, not just once
    for the whole film. FilmGenome.camera_language/color_language stay
    the film-wide baseline (spec section 6.3's shape, unchanged); a
    Sequence may declare its own to represent "this chapter looks and
    moves differently." None means "use the film's default" -- see
    production/builder.py's resolve_camera_language()/
    resolve_color_language()."""
    id: str
    song_section: str
    start_seconds: float
    end_seconds: float
    camera_language: CameraLanguage | None = None
    color_language: ColorLanguage | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "song_section": self.song_section,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "camera_language": self.camera_language.to_dict() if self.camera_language else None,
            "color_language": self.color_language.to_dict() if self.color_language else None,
        }

    @staticmethod
    def from_dict(data: dict) -> "Sequence":
        camera_language = data.get("camera_language")
        color_language = data.get("color_language")
        return Sequence(
            id=data["id"],
            song_section=data["song_section"],
            start_seconds=float(data["start_seconds"]),
            end_seconds=float(data["end_seconds"]),
            camera_language=CameraLanguage.from_dict(camera_language) if camera_language else None,
            color_language=ColorLanguage.from_dict(color_language) if color_language else None,
        )


@dataclass(frozen=True)
class ShotTiming:
    start_seconds: float
    end_seconds: float
    song_section: str
    lyric_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "song_section": self.song_section,
            "lyric_ids": list(self.lyric_ids),
        }

    @staticmethod
    def from_dict(data: dict) -> "ShotTiming":
        return ShotTiming(
            start_seconds=float(data["start_seconds"]),
            end_seconds=float(data["end_seconds"]),
            song_section=data["song_section"],
            lyric_ids=tuple(data.get("lyric_ids", [])),
        )


@dataclass(frozen=True)
class ShotPurpose:
    semantic_event_id: str
    narrative_function: str
    editorial_function: str

    def to_dict(self) -> dict:
        return {
            "semantic_event_id": self.semantic_event_id,
            "narrative_function": self.narrative_function,
            "editorial_function": self.editorial_function,
        }

    @staticmethod
    def from_dict(data: dict) -> "ShotPurpose":
        return ShotPurpose(
            semantic_event_id=data["semantic_event_id"],
            narrative_function=data["narrative_function"],
            editorial_function=data["editorial_function"],
        )


@dataclass(frozen=True)
class ShotRequirements:
    performer_id: str
    costume_id: str
    world_id: str
    lip_sync_required: bool
    choreography_complexity: str
    camera_motion: str
    character_count: int

    def to_dict(self) -> dict:
        return {
            "performer_id": self.performer_id,
            "costume_id": self.costume_id,
            "world_id": self.world_id,
            "lip_sync_required": self.lip_sync_required,
            "choreography_complexity": self.choreography_complexity,
            "camera_motion": self.camera_motion,
            "character_count": self.character_count,
        }

    @staticmethod
    def from_dict(data: dict) -> "ShotRequirements":
        return ShotRequirements(
            performer_id=data["performer_id"],
            costume_id=data["costume_id"],
            world_id=data["world_id"],
            lip_sync_required=bool(data["lip_sync_required"]),
            choreography_complexity=data["choreography_complexity"],
            camera_motion=data["camera_motion"],
            character_count=int(data["character_count"]),
        )


@dataclass(frozen=True)
class ShotContinuity:
    inherited_state: str
    permitted_mutations: tuple[str, ...]
    destination_state: str

    def to_dict(self) -> dict:
        return {
            "inherited_state": self.inherited_state,
            "permitted_mutations": list(self.permitted_mutations),
            "destination_state": self.destination_state,
        }

    @staticmethod
    def from_dict(data: dict) -> "ShotContinuity":
        return ShotContinuity(
            inherited_state=data["inherited_state"],
            permitted_mutations=tuple(data.get("permitted_mutations", [])),
            destination_state=data["destination_state"],
        )


@dataclass(frozen=True)
class Shot:
    id: str
    sequence_id: str
    timing: ShotTiming
    purpose: ShotPurpose
    requirements: ShotRequirements
    continuity: ShotContinuity
    acceptance: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sequence_id": self.sequence_id,
            "timing": self.timing.to_dict(),
            "purpose": self.purpose.to_dict(),
            "requirements": self.requirements.to_dict(),
            "continuity": self.continuity.to_dict(),
            "acceptance": dict(self.acceptance),
        }

    @staticmethod
    def from_dict(data: dict) -> "Shot":
        return Shot(
            id=data["id"],
            sequence_id=data["sequence_id"],
            timing=ShotTiming.from_dict(data["timing"]),
            purpose=ShotPurpose.from_dict(data["purpose"]),
            requirements=ShotRequirements.from_dict(data["requirements"]),
            continuity=ShotContinuity.from_dict(data["continuity"]),
            acceptance=dict(data.get("acceptance", {})),
        )


@dataclass(frozen=True)
class ProductionGraph:
    id: str
    film_genome_id: str
    sequences: tuple[Sequence, ...] = field(default_factory=tuple)
    semantic_events: tuple[SemanticEvent, ...] = field(default_factory=tuple)
    shots: tuple[Shot, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "film_genome_id": self.film_genome_id,
            "sequences": [sequence.to_dict() for sequence in self.sequences],
            "semantic_events": [event.to_dict() for event in self.semantic_events],
            "shots": [shot.to_dict() for shot in self.shots],
        }

    @staticmethod
    def from_dict(data: dict) -> "ProductionGraph":
        return ProductionGraph(
            id=data["id"],
            film_genome_id=data["film_genome_id"],
            sequences=tuple(Sequence.from_dict(item) for item in data.get("sequences", [])),
            semantic_events=tuple(SemanticEvent.from_dict(item) for item in data.get("semantic_events", [])),
            shots=tuple(Shot.from_dict(item) for item in data.get("shots", [])),
        )
