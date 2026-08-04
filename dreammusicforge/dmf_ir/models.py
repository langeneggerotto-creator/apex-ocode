"""DMF-IR v1 typed models.

Dataclasses mirroring schema.py's contract. These exist so every downstream
compiler works against typed objects instead of re-parsing raw dicts by
hand -- one canonical representation, not one per compiler.

parse_project() assumes the input already passed
validator.validate_schema() -- it does not re-check required fields itself
(that would duplicate schema.py's contract in a second place). Call
validator.validate() first, as compiler.compile() does.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Film:
    id: str
    title: str
    duration_seconds: float
    aspect_ratio: str
    frame_rate: float
    style_identity: str


@dataclass(frozen=True)
class Character:
    id: str
    identity_locked: bool
    wardrobe_id: str


@dataclass(frozen=True)
class World:
    id: str
    persistent: bool


@dataclass(frozen=True)
class MusicEvent:
    id: str
    start: float
    end: float
    section: str


@dataclass(frozen=True)
class SemanticEvent:
    id: str
    start: float
    end: float
    meaning: str


@dataclass(frozen=True)
class RealityState:
    id: str
    timecode: float
    extra: dict[str, Any] = field(default_factory=dict)
    """Free-form state beyond id/timecode (notebook, emotion, new_line, ...) --
    see schema.py's note on why reality_states is not fully schema-constrained."""


@dataclass(frozen=True)
class VerificationContract:
    id: str
    pass_threshold: float
    reject_if: tuple[str, ...]


@dataclass(frozen=True)
class Clip:
    id: str
    start: float
    end: float
    source_state_id: str
    destination_state_id: str
    semantic_event_ids: tuple[str, ...]
    music_event_ids: tuple[str, ...]
    primary_action: str
    secondary_actions: tuple[str, ...]
    maximum_actions: int
    continuity_mode: str
    required_reference_assets: tuple[str, ...]
    verification_contract_id: str

    @property
    def duration_seconds(self) -> float:
        return self.end - self.start

    @property
    def total_actions(self) -> int:
        return 1 + len(self.secondary_actions)


@dataclass(frozen=True)
class DMFProject:
    schema_version: str
    film: Film
    characters: tuple[Character, ...]
    worlds: tuple[World, ...]
    music_events: tuple[MusicEvent, ...]
    semantic_events: tuple[SemanticEvent, ...]
    reality_states: tuple[RealityState, ...]
    clips: tuple[Clip, ...]
    verification_contracts: tuple[VerificationContract, ...]

    def clips_in_order(self) -> tuple[Clip, ...]:
        return tuple(sorted(self.clips, key=lambda clip: clip.start))

    def index_characters(self) -> dict[str, Character]:
        return {item.id: item for item in self.characters}

    def index_worlds(self) -> dict[str, World]:
        return {item.id: item for item in self.worlds}

    def index_music_events(self) -> dict[str, MusicEvent]:
        return {item.id: item for item in self.music_events}

    def index_semantic_events(self) -> dict[str, SemanticEvent]:
        return {item.id: item for item in self.semantic_events}

    def index_reality_states(self) -> dict[str, RealityState]:
        return {item.id: item for item in self.reality_states}

    def index_verification_contracts(self) -> dict[str, VerificationContract]:
        return {item.id: item for item in self.verification_contracts}


def _known_keys(item: dict[str, Any], *known: str) -> dict[str, Any]:
    return {k: v for k, v in item.items() if k not in known}


def parse_film(data: dict) -> Film:
    return Film(
        id=data["id"], title=data["title"], duration_seconds=float(data["duration_seconds"]),
        aspect_ratio=data["aspect_ratio"], frame_rate=float(data["frame_rate"]),
        style_identity=data["style_identity"],
    )


def parse_character(data: dict) -> Character:
    return Character(id=data["id"], identity_locked=bool(data["identity_locked"]), wardrobe_id=data["wardrobe_id"])


def parse_world(data: dict) -> World:
    return World(id=data["id"], persistent=bool(data["persistent"]))


def parse_music_event(data: dict) -> MusicEvent:
    return MusicEvent(id=data["id"], start=float(data["start"]), end=float(data["end"]), section=data["section"])


def parse_semantic_event(data: dict) -> SemanticEvent:
    return SemanticEvent(id=data["id"], start=float(data["start"]), end=float(data["end"]), meaning=data["meaning"])


def parse_reality_state(data: dict) -> RealityState:
    return RealityState(id=data["id"], timecode=float(data["timecode"]), extra=_known_keys(data, "id", "timecode"))


def parse_verification_contract(data: dict) -> VerificationContract:
    return VerificationContract(
        id=data["id"], pass_threshold=float(data["pass_threshold"]),
        reject_if=tuple(data["reject_if"]),
    )


def parse_clip(data: dict) -> Clip:
    return Clip(
        id=data["id"], start=float(data["start"]), end=float(data["end"]),
        source_state_id=data["source_state_id"], destination_state_id=data["destination_state_id"],
        semantic_event_ids=tuple(data.get("semantic_event_ids", [])),
        music_event_ids=tuple(data.get("music_event_ids", [])),
        primary_action=data["primary_action"],
        secondary_actions=tuple(data.get("secondary_actions", [])),
        maximum_actions=int(data.get("maximum_actions", 1)),
        continuity_mode=data["continuity_mode"],
        required_reference_assets=tuple(data.get("required_reference_assets", [])),
        verification_contract_id=data["verification_contract_id"],
    )


def parse_project(data: dict, *, schema_version: str | None = None) -> DMFProject:
    from .schema import DMF_IR_SCHEMA_VERSION

    return DMFProject(
        schema_version=data.get("schema_version", schema_version or DMF_IR_SCHEMA_VERSION),
        film=parse_film(data["film"]),
        characters=tuple(parse_character(item) for item in data["characters"]),
        worlds=tuple(parse_world(item) for item in data["worlds"]),
        music_events=tuple(parse_music_event(item) for item in data["music_events"]),
        semantic_events=tuple(parse_semantic_event(item) for item in data["semantic_events"]),
        reality_states=tuple(parse_reality_state(item) for item in data["reality_states"]),
        clips=tuple(parse_clip(item) for item in data["clips"]),
        verification_contracts=tuple(parse_verification_contract(item) for item in data["verification_contracts"]),
    )
