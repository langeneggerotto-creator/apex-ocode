"""compile_kling_package()/compile_kling_packages(): turn a RenderTask
(Release 0.6) plus its Shot (Release 0.4) into an operator-usable
KlingPackage -- this release's acceptance test from spec section 19:
"each task produces an operator-usable Kling package."

Mode selection is deterministic: a RenderTask whose required_assets
includes a `.mp4` reference is a continuation task (Release 0.6's
controlled_continuation strategy chains each task after the first to
the previous one's output file -- see slicer/builder.py), so it compiles
to `video_extension`; everything else compiles to `image_to_video`,
since Performer/Costume/World reference assets (Release 0.3) are
reference images. If the resulting mode isn't in the given
KlingProfile.supported_modes, compilation fails closed rather than
silently choosing something the profile doesn't declare support for.

The prompt template adapts this same repository's pre-spec `runtime.py`
`compile_kling_packages()` -- same structural pattern (explicit
continuity statement, explicit "do not perform future actions", explicit
preservation list), rewritten against the new typed Shot fields instead
of runtime.py's dict-shaped clips. `KLING_NEGATIVE_PROMPT_BASELINE` is
copied from that same function verbatim.
"""
from __future__ import annotations

from ...production.models import Shot
from ...slicer.models import RenderTask
from .errors import KlingCompilerError
from .ids import generate_kling_package_id
from .models import KLING_NEGATIVE_PROMPT_BASELINE, KlingPackage, KlingProfile
from .schema import validate_kling_package_schema

_CONTINUATION_ASSET_SUFFIX = ".mp4"


def _select_mode(render_task: RenderTask, profile: KlingProfile) -> str:
    is_continuation = any(asset.endswith(_CONTINUATION_ASSET_SUFFIX) for asset in render_task.required_assets)
    mode = "video_extension" if is_continuation else "image_to_video"
    if mode not in profile.supported_modes:
        raise KlingCompilerError([f"mode {mode!r} required for render_task {render_task.id!r} is not in this KlingProfile's supported_modes {list(profile.supported_modes)}"])
    return mode


def _build_prompt(render_task: RenderTask, shot: Shot, mode: str) -> str:
    lines = [
        f"Create {render_task.duration_seconds:.1f} seconds of cinematic video.",
        f"Mode: {mode}.",
        "Do not rely on memory from prior generations.",
        "Treat supplied reference images, videos, and Elements as binding references.",
        f"Song section: {shot.timing.song_section}.",
        f"Inherited state: {shot.continuity.inherited_state}.",
        f"Perform this shot's dominant action toward: {shot.purpose.narrative_function}.",
        "Do not perform any future action.",
        f"Destination state: {shot.continuity.destination_state}.",
        f"Editorial function: {shot.purpose.editorial_function}.",
        f"Camera motion: {shot.requirements.camera_motion}.",
        f"Choreography complexity: {shot.requirements.choreography_complexity}.",
        "The song is the master clock; continue its phrase and energy without reset.",
        "Preserve character identity, wardrobe, world, props, camera axis, lighting direction, and emotional momentum.",
        "Use natural body mechanics and end on a stable frame suitable for the next clip.",
    ]
    return "\n".join(lines) + "\n"


def _build_reference_manifest(render_task: RenderTask, reference_manifest_overrides: dict[str, tuple[str, ...]] | None) -> tuple[str, ...]:
    overrides = reference_manifest_overrides or {}
    manifest: list[str] = []
    for asset in render_task.required_assets:
        manifest.extend(overrides.get(asset, (asset,)))
    return tuple(manifest)


def compile_kling_package(
    render_task: RenderTask,
    shot: Shot,
    profile: KlingProfile,
    reference_manifest_overrides: dict[str, tuple[str, ...]] | None = None,
    package_id: str | None = None,
) -> KlingPackage:
    if render_task.shot_id != shot.id:
        raise KlingCompilerError([f"render_task {render_task.id!r} belongs to shot {render_task.shot_id!r}, not {shot.id!r}"])
    if render_task.duration_seconds > profile.max_duration_seconds:
        raise KlingCompilerError([
            f"render_task {render_task.id!r} duration_seconds {render_task.duration_seconds} "
            f"exceeds KlingProfile.max_duration_seconds {profile.max_duration_seconds}"
        ])

    mode = _select_mode(render_task, profile)
    package = KlingPackage(
        id=package_id or generate_kling_package_id(),
        render_task_id=render_task.id,
        shot_id=shot.id,
        mode=mode,
        duration_seconds=render_task.duration_seconds,
        duration_limit_seconds=profile.max_duration_seconds,
        prompt=_build_prompt(render_task, shot, mode),
        negative_prompt=KLING_NEGATIVE_PROMPT_BASELINE,
        reference_manifest=_build_reference_manifest(render_task, reference_manifest_overrides),
    )

    errors = validate_kling_package_schema(package.to_dict())
    if errors:
        raise KlingCompilerError(errors)
    return package


def compile_kling_packages(
    render_tasks: tuple[RenderTask, ...],
    shot: Shot,
    profile: KlingProfile,
    reference_manifest_overrides: dict[str, tuple[str, ...]] | None = None,
) -> tuple[KlingPackage, ...]:
    return tuple(
        compile_kling_package(render_task, shot, profile, reference_manifest_overrides)
        for render_task in render_tasks
    )
