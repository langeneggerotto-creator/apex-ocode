"""DreamMusicForge Film Compiler -- genome package (Release 0.3).

Public API:

    from dreammusicforge.genome import (
        Performer, Costume, World, CameraLanguage, ColorLanguage, FilmGenome,
        generate_performer_id, is_valid_performer_id,
        generate_costume_id, is_valid_costume_id,
        generate_world_id, is_valid_world_id,
        generate_genome_id, is_valid_genome_id,
        validate_performer_schema, validate_costume_schema,
        validate_world_schema, validate_film_genome_schema,
        build_performer, build_costume, build_world, assemble_film_genome,
        GenomeValidationError,
    )

Everything else in the full spec (Production Graph, Video Slicer,
provider compilers, verification, repair, assembly, ...) is later
releases and is not present here.
"""
from __future__ import annotations

from .builder import assemble_film_genome, build_costume, build_performer, build_world
from .errors import GenomeValidationError
from .ids import (
    generate_costume_id, generate_genome_id, generate_performer_id, generate_world_id,
    is_valid_costume_id, is_valid_genome_id, is_valid_performer_id, is_valid_world_id,
)
from .models import CameraLanguage, ColorLanguage, Costume, FilmGenome, Performer, World
from .schema import (
    validate_costume_schema, validate_film_genome_schema, validate_performer_schema, validate_world_schema,
)

__all__ = [
    "CameraLanguage", "ColorLanguage", "Costume", "FilmGenome", "GenomeValidationError",
    "Performer", "World", "assemble_film_genome", "build_costume", "build_performer", "build_world",
    "generate_costume_id", "generate_genome_id", "generate_performer_id", "generate_world_id",
    "is_valid_costume_id", "is_valid_genome_id", "is_valid_performer_id", "is_valid_world_id",
    "validate_costume_schema", "validate_film_genome_schema", "validate_performer_schema",
    "validate_world_schema",
]
