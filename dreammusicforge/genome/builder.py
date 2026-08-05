"""Assembly helpers: the functions that turn Performer/Costume/World
definitions plus declared genome-level facts (transformation arc, camera
language, color language, motifs, invariants) into a validated
FilmGenome -- this release's acceptance test from spec section 19: "a
complete Film Genome can be created and validated."

Every function here validates its own output against genome/schema.py
before returning it, so a caller can never hold a Performer, Costume,
World, or FilmGenome that wouldn't itself pass validation -- fail
closed, same discipline as music/builder.py.

assemble_film_genome() derives performer_ids/costume_ids/world_ids
directly from the Performer/Costume/World objects it's given, rather
than accepting id lists separately -- see genome/schema.py's module
docstring for why that's how this release enforces spec Law 3.7 ("fail
closed" on missing references): a FilmGenome built through this
function cannot reference a nonexistent entity, by construction.
"""
from __future__ import annotations

from .errors import GenomeValidationError
from .ids import generate_costume_id, generate_genome_id, generate_performer_id, generate_world_id
from .models import CameraLanguage, ColorLanguage, Costume, FilmGenome, Performer, World
from .schema import (
    validate_costume_schema, validate_film_genome_schema, validate_performer_schema, validate_world_schema,
)


def build_performer(
    display_name: str,
    reference_assets: tuple[str, ...],
    immutable: dict[str, str],
    mutable_by_contract: dict[str, str],
    performer_id: str | None = None,
) -> Performer:
    performer = Performer(
        id=performer_id or generate_performer_id(),
        display_name=display_name,
        reference_assets=tuple(reference_assets),
        immutable=dict(immutable),
        mutable_by_contract=dict(mutable_by_contract),
    )

    errors = validate_performer_schema(performer.to_dict())
    if errors:
        raise GenomeValidationError(errors)
    return performer


def build_costume(
    topology: dict[str, str],
    material: str,
    references: dict[str, str],
    embroidery: str | None = None,
    accessories: dict[str, str] | None = None,
    costume_id: str | None = None,
) -> Costume:
    costume = Costume(
        id=costume_id or generate_costume_id(),
        topology=dict(topology),
        material=material,
        references=dict(references),
        embroidery=embroidery,
        accessories=dict(accessories or {}),
    )

    errors = validate_costume_schema(costume.to_dict())
    if errors:
        raise GenomeValidationError(errors)
    return costume


def build_world(
    type: str,
    references: dict[str, str],
    geometry: str,
    palette: str,
    lighting: str,
    atmosphere: str,
    props: tuple[str, ...] = (),
    allowed_transformations: tuple[str, ...] = (),
    forbidden_transformations: tuple[str, ...] = (),
    world_id: str | None = None,
) -> World:
    world = World(
        id=world_id or generate_world_id(),
        type=type,
        references=dict(references),
        geometry=geometry,
        palette=palette,
        lighting=lighting,
        atmosphere=atmosphere,
        props=tuple(props),
        allowed_transformations=tuple(allowed_transformations),
        forbidden_transformations=tuple(forbidden_transformations),
    )

    errors = validate_world_schema(world.to_dict())
    if errors:
        raise GenomeValidationError(errors)
    return world


def assemble_film_genome(
    transformation_from: str,
    transformation_to: str,
    performers: tuple[Performer, ...],
    costumes: tuple[Costume, ...],
    worlds: tuple[World, ...],
    camera_language: CameraLanguage,
    color_language: ColorLanguage,
    motifs: tuple[str, ...],
    invariants: tuple[str, ...],
    genome_id: str | None = None,
) -> FilmGenome:
    genome = FilmGenome(
        id=genome_id or generate_genome_id(),
        transformation_from=transformation_from,
        transformation_to=transformation_to,
        performer_ids=tuple(performer.id for performer in performers),
        costume_ids=tuple(costume.id for costume in costumes),
        world_ids=tuple(world.id for world in worlds),
        camera_language=camera_language,
        color_language=color_language,
        motifs=tuple(motifs),
        invariants=tuple(invariants),
    )

    errors = validate_film_genome_schema(genome.to_dict())
    if errors:
        raise GenomeValidationError(errors)
    return genome
