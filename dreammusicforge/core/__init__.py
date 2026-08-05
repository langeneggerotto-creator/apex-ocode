"""DreamMusicForge Film Compiler -- kernel package (Release 0.1).

Public API:

    from dreammusicforge.core import (
        Project, PROJECT_STATUSES,
        validate_project_schema, PROJECT_SCHEMA, PROJECT_SCHEMA_VERSION,
        generate_project_id, validate_project_id, is_valid_project_id,
        confine_path,
        hash_bytes, hash_text, hash_file,
        DMFError, ProjectValidationError, ProjectNotFoundError,
        ProjectAlreadyExistsError, InvalidProjectIdError, PathConfinementError,
    )

Everything else in the full spec (Film Genome, Production Graph, Master
Song analysis, slicer, providers, verification, assembly, ...) is later
releases and is not present here.
"""
from __future__ import annotations

from .errors import (
    DMFError, InvalidProjectIdError, PathConfinementError, ProjectAlreadyExistsError,
    ProjectNotFoundError, ProjectValidationError,
)
from .hashing import hash_bytes, hash_file, hash_text
from .ids import generate_project_id, is_valid_project_id, validate_project_id
from .models import PROJECT_STATUSES, Project
from .paths import confine_path
from .schema import PROJECT_SCHEMA, PROJECT_SCHEMA_VERSION, validate_project_schema

__all__ = [
    "DMFError", "InvalidProjectIdError", "PathConfinementError", "PROJECT_SCHEMA",
    "PROJECT_SCHEMA_VERSION", "PROJECT_STATUSES", "Project", "ProjectAlreadyExistsError",
    "ProjectNotFoundError", "ProjectValidationError", "confine_path", "generate_project_id",
    "hash_bytes", "hash_file", "hash_text", "is_valid_project_id", "validate_project_id",
    "validate_project_schema",
]
