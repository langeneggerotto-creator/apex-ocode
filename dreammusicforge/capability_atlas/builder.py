"""Construction helpers that validate their own output before
returning it, same discipline as music/builder.py, genome/builder.py,
and production/builder.py."""
from __future__ import annotations

from .errors import CapabilityAtlasValidationError
from .models import RendererCapability, RendererCapabilityProfile
from .schema import validate_capability_profile_schema, validate_capability_schema


def build_capability(name: str, status: str, evidence: str | None = None) -> RendererCapability:
    capability = RendererCapability(name=name, status=status, evidence=evidence)

    errors = validate_capability_schema(capability.to_dict())
    if errors:
        raise CapabilityAtlasValidationError(errors)
    return capability


def build_capability_profile(
    provider: str,
    max_duration_seconds: float,
    max_character_count: int,
    supported_camera_motions: tuple[str, ...],
    capabilities: tuple[RendererCapability, ...] = (),
) -> RendererCapabilityProfile:
    profile = RendererCapabilityProfile(
        provider=provider,
        max_duration_seconds=max_duration_seconds,
        max_character_count=max_character_count,
        supported_camera_motions=tuple(supported_camera_motions),
        capabilities=tuple(capabilities),
    )

    errors = validate_capability_profile_schema(profile.to_dict())
    if errors:
        raise CapabilityAtlasValidationError(errors)
    return profile
