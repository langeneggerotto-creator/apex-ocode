"""DMF-IR v1: the canonical, provider-neutral DreamMusicForge intermediate
representation. Every future compiler (music, continuity, cinematography,
editing, verification, provider adapters) should read from this, not from
ad hoc dict access on raw project JSON.

    from dreammusicforge.dmf_ir import validate, compile, parse_project

Public API:

- schema.DMF_IR_SCHEMA / DMF_IR_SCHEMA_VERSION -- the contract, as data.
- models.parse_project(data) -> DMFProject -- typed parse (assumes valid).
- validator.validate(data) -> ValidationResult -- schema + semantic checks.
- compiler.compile(data) -> CompiledContinuityPlan -- validates, then
  compiles into the provider-neutral Continuity Compiler stage.
"""
from __future__ import annotations

from .compiler import CompiledClip, CompiledContinuityPlan, compile, compile_project
from .models import (
    Character, Clip, DMFProject, Film, MusicEvent, RealityState,
    SemanticEvent, VerificationContract, World, parse_project,
)
from .schema import CONTINUITY_MODES, DMF_IR_SCHEMA, DMF_IR_SCHEMA_VERSION
from .validator import validate, validate_schema, validate_semantics

__all__ = [
    "CONTINUITY_MODES", "DMF_IR_SCHEMA", "DMF_IR_SCHEMA_VERSION",
    "Character", "Clip", "CompiledClip", "CompiledContinuityPlan", "DMFProject",
    "Film", "MusicEvent", "RealityState", "SemanticEvent", "VerificationContract", "World",
    "compile", "compile_project", "parse_project", "validate", "validate_schema", "validate_semantics",
]
