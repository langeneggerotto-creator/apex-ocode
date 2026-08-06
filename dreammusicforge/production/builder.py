"""Assembly helpers: the functions that turn Sequence/SemanticEvent/Shot
definitions plus a FilmGenome into a validated, ordered ProductionGraph
-- this release's acceptance test from spec section 19: "project
compiles into an ordered production graph."

build_semantic_event()/build_sequence()/build_shot() each validate
their own output against production/schema.py before returning it.
assemble_production_graph() additionally checks that every
requirements.performer_id/costume_id/world_id a Shot references actually
exists in the given FilmGenome -- the one check production/schema.py
cannot make on its own, since a FilmGenome isn't part of the
production_graph dict (see production/schema.py's module docstring) --
and it orders the resulting shots by timing.start_seconds, which is
what "compiles into an *ordered* production graph" means here: the
compiler imposes the order, callers don't have to pre-sort their input.
"""
from __future__ import annotations

from ..genome.models import CameraLanguage, ColorLanguage, FilmGenome
from .errors import ProductionGraphValidationError
from .ids import generate_graph_id, generate_semantic_event_id, generate_sequence_id, generate_shot_id
from .models import (
    ProductionGraph, SemanticEvent, Sequence, Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming,
)
from .schema import validate_production_graph_schema, validate_semantic_event_schema, validate_sequence_schema, validate_shot_schema


def build_semantic_event(
    start_seconds: float,
    end_seconds: float,
    meaning: str,
    transformation_from: str,
    transformation_to: str,
    intended_viewer_inference: tuple[str, ...] = (),
    required_visible_evidence: tuple[str, ...] = (),
    event_id: str | None = None,
) -> SemanticEvent:
    event = SemanticEvent(
        id=event_id or generate_semantic_event_id(),
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        meaning=meaning,
        transformation_from=transformation_from,
        transformation_to=transformation_to,
        intended_viewer_inference=tuple(intended_viewer_inference),
        required_visible_evidence=tuple(required_visible_evidence),
    )

    errors = validate_semantic_event_schema(event.to_dict())
    if errors:
        raise ProductionGraphValidationError(errors)
    return event


def build_sequence(
    song_section: str,
    start_seconds: float,
    end_seconds: float,
    sequence_id: str | None = None,
    camera_language: CameraLanguage | None = None,
    color_language: ColorLanguage | None = None,
) -> Sequence:
    sequence = Sequence(
        id=sequence_id or generate_sequence_id(),
        song_section=song_section,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        camera_language=camera_language,
        color_language=color_language,
    )

    errors = validate_sequence_schema(sequence.to_dict())
    if errors:
        raise ProductionGraphValidationError(errors)
    return sequence


def resolve_camera_language(sequence: Sequence, film_genome: FilmGenome) -> CameraLanguage:
    """A sequence's own camera_language if it declared one (a chapter
    that deliberately moves differently from the rest of the film),
    otherwise the film's default -- see Sequence's docstring for why
    this override exists."""
    return sequence.camera_language if sequence.camera_language is not None else film_genome.camera_language


def resolve_color_language(sequence: Sequence, film_genome: FilmGenome) -> ColorLanguage:
    """A sequence's own color_language if it declared one, otherwise
    the film's default -- see resolve_camera_language()."""
    return sequence.color_language if sequence.color_language is not None else film_genome.color_language


def build_shot(
    sequence_id: str,
    timing: ShotTiming,
    purpose: ShotPurpose,
    requirements: ShotRequirements,
    continuity: ShotContinuity,
    acceptance: dict[str, float],
    shot_id: str | None = None,
) -> Shot:
    shot = Shot(
        id=shot_id or generate_shot_id(),
        sequence_id=sequence_id,
        timing=timing,
        purpose=purpose,
        requirements=requirements,
        continuity=continuity,
        acceptance=dict(acceptance),
    )

    errors = validate_shot_schema(shot.to_dict())
    if errors:
        raise ProductionGraphValidationError(errors)
    return shot


def assemble_production_graph(
    film_genome: FilmGenome,
    sequences: tuple[Sequence, ...],
    semantic_events: tuple[SemanticEvent, ...],
    shots: tuple[Shot, ...],
    graph_id: str | None = None,
) -> ProductionGraph:
    ordered_shots = tuple(sorted(shots, key=lambda shot: shot.timing.start_seconds))

    graph = ProductionGraph(
        id=graph_id or generate_graph_id(),
        film_genome_id=film_genome.id,
        sequences=tuple(sorted(sequences, key=lambda sequence: sequence.start_seconds)),
        semantic_events=tuple(sorted(semantic_events, key=lambda event: event.start_seconds)),
        shots=ordered_shots,
    )

    errors = list(validate_production_graph_schema(graph.to_dict()))

    performer_ids = set(film_genome.performer_ids)
    costume_ids = set(film_genome.costume_ids)
    world_ids = set(film_genome.world_ids)
    for shot in ordered_shots:
        if shot.requirements.performer_id not in performer_ids:
            errors.append(f"shot {shot.id!r} requires performer_id {shot.requirements.performer_id!r}, which is not in film_genome {film_genome.id!r}")
        if shot.requirements.costume_id not in costume_ids:
            errors.append(f"shot {shot.id!r} requires costume_id {shot.requirements.costume_id!r}, which is not in film_genome {film_genome.id!r}")
        if shot.requirements.world_id not in world_ids:
            errors.append(f"shot {shot.id!r} requires world_id {shot.requirements.world_id!r}, which is not in film_genome {film_genome.id!r}")

    if errors:
        raise ProductionGraphValidationError(errors)
    return graph
