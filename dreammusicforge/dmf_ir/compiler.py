"""DMF-IR v1 compiler: the Continuity Compiler stage.

Sits between DMF-IR (validated project data) and any provider compiler
(runtime.compile_kling_packages today, others later) in the pipeline:

    DMF-IR --validate--> DMFProject --compile--> CompiledContinuityPlan --[provider compiler]--> provider package

Provider-neutral by construction: a CompiledClip expresses what a clip
depends on (dependency_kind: none / reference_assets_only /
verified_end_frame / full_video) and what it must preserve, not how any one
provider names its asset files or what its API call looks like. A Kling
compiler turns "verified_end_frame, depends_on=CLIP-001" into
"CLIP-001-VERIFIED-END.png"; a different provider could turn the same
dependency into something else entirely without this module changing.

This module does not replace runtime.compile_kling_packages -- that
function, and its tests, are untouched and continue to work exactly as
before. This is the new, stricter, canonical layer future compilers should
build on; providers can migrate to consuming it incrementally.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import (
    Clip, DMFProject, Film, MusicEvent, RealityState, SemanticEvent,
    VerificationContract, parse_project,
)
from .schema import CONTINUITY_MODES
from .validator import validate


@dataclass(frozen=True)
class CompiledClip:
    clip_id: str
    order: int
    duration_seconds: float
    continuity_mode: str
    dependency_kind: str
    """One of schema.CONTINUITY_MODES' values: none / reference_assets_only /
    verified_end_frame / full_video."""
    depends_on_clip_id: str | None
    source_state: RealityState
    destination_state: RealityState
    semantic_events: tuple[SemanticEvent, ...]
    music_events: tuple[MusicEvent, ...]
    primary_action: str
    secondary_actions: tuple[str, ...]
    verification_contract: VerificationContract
    required_reference_ids: tuple[str, ...]
    """De-duplicated, order-preserved character/world ids this clip must be
    conditioned on, already validated to exist."""


@dataclass(frozen=True)
class CompiledContinuityPlan:
    schema_version: str
    film: Film
    clips: tuple[CompiledClip, ...]


def _compile_clip(clip: Clip, order: int, previous: Clip | None, project: DMFProject) -> CompiledClip:
    semantics = project.index_semantic_events()
    music = project.index_music_events()
    states = project.index_reality_states()
    checks = project.index_verification_contracts()

    dependency_kind = CONTINUITY_MODES[clip.continuity_mode]
    depends_on_clip_id = previous.id if (previous is not None and dependency_kind != "none") else None

    seen: set[str] = set()
    required_reference_ids: list[str] = []
    for asset_id in clip.required_reference_assets:
        if asset_id not in seen:
            seen.add(asset_id)
            required_reference_ids.append(asset_id)

    return CompiledClip(
        clip_id=clip.id,
        order=order,
        duration_seconds=clip.duration_seconds,
        continuity_mode=clip.continuity_mode,
        dependency_kind=dependency_kind,
        depends_on_clip_id=depends_on_clip_id,
        source_state=states[clip.source_state_id],
        destination_state=states[clip.destination_state_id],
        semantic_events=tuple(semantics[event_id] for event_id in clip.semantic_event_ids),
        music_events=tuple(music[event_id] for event_id in clip.music_event_ids),
        primary_action=clip.primary_action,
        secondary_actions=clip.secondary_actions,
        verification_contract=checks[clip.verification_contract_id],
        required_reference_ids=tuple(required_reference_ids),
    )


def compile_project(project: DMFProject, max_clip_seconds: float = 15.0) -> CompiledContinuityPlan:
    """Compile an already-parsed DMFProject. Callers who have raw dict data
    should use compile() instead, which validates first -- this function
    assumes project is valid and does not re-validate."""
    clips = project.clips_in_order()
    compiled: list[CompiledClip] = []
    previous: Clip | None = None
    for order, clip in enumerate(clips, start=1):
        compiled.append(_compile_clip(clip, order, previous, project))
        previous = clip
    return CompiledContinuityPlan(schema_version=project.schema_version, film=project.film, clips=tuple(compiled))


def compile(data: dict, max_clip_seconds: float = 15.0) -> CompiledContinuityPlan:
    """Validate raw DMF-IR project data, then compile it. Raises ValueError
    with every validation error joined, matching
    runtime.compile_kling_packages' fail-closed behavior on invalid input."""
    result = validate(data, max_clip_seconds=max_clip_seconds)
    if not result.valid:
        raise ValueError("Invalid DMF-IR project:\n- " + "\n- ".join(result.errors))
    project = parse_project(data)
    return compile_project(project, max_clip_seconds=max_clip_seconds)
