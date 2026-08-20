"""DreamMusicForge Film Compiler -- providers.runway package.

Not part of the original spec's numbered release plan (the spec only
names Kling); added because the user asked to connect Runway as a
second video-generation provider, mirroring providers.kling's Release
0.7 architecture. See models.py's module docstring for what's real
(request/response shapes grounded in Runway's public API docs) versus
disclosed as untested (no live API call was made in this session --
see client.py's module docstring).

Public API:

    from dreammusicforge.providers.runway import (
        RUNWAY_MODES, RUNWAY_MODELS, RUNWAY_RATIOS, RUNWAY_DURATION_OPTIONS_SECONDS,
        RunwayProfile, RunwayPackage,
        compile_runway_package, compile_runway_packages,
        RunwayClient,
        validate_runway_profile_schema, validate_runway_package_schema,
        generate_runway_package_id, is_valid_runway_package_id,
        RunwayCompilerError, RunwayClientError,
    )

Same one-way-dependency discipline as providers.kling: this package
imports production.models.Shot and slicer.models.RenderTask, never the
reverse -- no other package in this repository imports from
providers.runway.
"""
from __future__ import annotations

from .client import RunwayClient
from .compiler import compile_runway_package, compile_runway_packages
from .errors import RunwayClientError, RunwayCompilerError
from .ids import generate_runway_package_id, is_valid_runway_package_id
from .models import (
    RUNWAY_DURATION_OPTIONS_SECONDS, RUNWAY_MODELS, RUNWAY_MODES, RUNWAY_RATIOS, RunwayPackage, RunwayProfile,
)
from .schema import validate_runway_package_schema, validate_runway_profile_schema

__all__ = [
    "RUNWAY_DURATION_OPTIONS_SECONDS", "RUNWAY_MODELS", "RUNWAY_MODES", "RUNWAY_RATIOS", "RunwayClient",
    "RunwayClientError", "RunwayCompilerError", "RunwayPackage", "RunwayProfile", "compile_runway_package",
    "compile_runway_packages", "generate_runway_package_id", "is_valid_runway_package_id",
    "validate_runway_package_schema", "validate_runway_profile_schema",
]
