"""DreamMusicForge Film Compiler -- providers.kling package (Release 0.7).

Public API:

    from dreammusicforge.providers.kling import (
        KLING_MODES, KLING_NEGATIVE_PROMPT_BASELINE, KlingProfile, KlingPackage,
        compile_kling_package, compile_kling_packages,
        validate_kling_profile_schema, validate_kling_package_schema,
        generate_kling_package_id, is_valid_kling_package_id,
        KlingCompilerError,
    )

Everything else in the full spec (candidate intake, verification,
repair, assembly, ...) is later releases and is not present here. No
other package in this repository imports from `providers.kling` --
per spec section 14 ("No core compiler module may import Kling-specific
implementation details"), the dependency runs one way: this package
imports `production.models.Shot` and `slicer.models.RenderTask`, never
the reverse.
"""
from __future__ import annotations

from .compiler import compile_kling_package, compile_kling_packages
from .errors import KlingCompilerError
from .ids import generate_kling_package_id, is_valid_kling_package_id
from .models import KLING_MODES, KLING_NEGATIVE_PROMPT_BASELINE, KlingPackage, KlingProfile
from .schema import validate_kling_package_schema, validate_kling_profile_schema

__all__ = [
    "KLING_MODES", "KLING_NEGATIVE_PROMPT_BASELINE", "KlingCompilerError", "KlingPackage", "KlingProfile",
    "compile_kling_package", "compile_kling_packages", "generate_kling_package_id", "is_valid_kling_package_id",
    "validate_kling_package_schema", "validate_kling_profile_schema",
]
