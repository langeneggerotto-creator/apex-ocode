"""DreamMusicForge Film Compiler -- assembly package (Release 0.11).

Public API:

    from dreammusicforge.assembly import (
        TRANSITION_TYPES, EXECUTABLE_TRANSITION_TYPES,
        Transition, AssembledClip, ExportManifest,
        normalize_clip, concatenate_clips, replace_audio, assemble_film,
        validate_transition_schema, validate_assembled_clip_schema, validate_export_manifest_schema,
        generate_export_id, is_valid_export_id,
        AssemblyError,
    )

Everything else in the full spec (lip-sync, masking/compositing, color/
audio finishing, ...) is later releases and is not present here.
"""
from __future__ import annotations

from .builder import assemble_film
from .errors import AssemblyError
from .ids import generate_export_id, is_valid_export_id
from .models import EXECUTABLE_TRANSITION_TYPES, TRANSITION_TYPES, AssembledClip, ExportManifest, Transition
from .pipeline import concatenate_clips, normalize_clip, replace_audio
from .schema import validate_assembled_clip_schema, validate_export_manifest_schema, validate_transition_schema

__all__ = [
    "AssembledClip", "AssemblyError", "EXECUTABLE_TRANSITION_TYPES", "ExportManifest", "TRANSITION_TYPES",
    "Transition", "assemble_film", "concatenate_clips", "generate_export_id", "is_valid_export_id",
    "normalize_clip", "replace_audio", "validate_assembled_clip_schema", "validate_export_manifest_schema",
    "validate_transition_schema",
]
