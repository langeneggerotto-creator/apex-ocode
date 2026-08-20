"""compile_runway_package()/compile_runway_packages(): turn a
RenderTask (Release 0.6) plus its Shot (Release 0.4) into an
operator-usable RunwayPackage -- the same "one RenderTask compiles to
one operator-usable provider package" shape Release 0.7 established
for Kling, adapted to Runway's real API constraints.

Unlike Kling's compiler, mode/image selection here is NOT sniffed from
`RenderTask.required_assets`: this repository's own slicer/builder.py
always populates that field with entity ids
(`performer_id`/`costume_id`/`world_id`), never a resolved image file
path (see `slicer/builder.py`'s `_required_assets()`) -- there is
nothing there to sniff a real Runway `promptImage` URL out of. Runway's
real `image_to_video` endpoint requires one concrete image URL as a
request parameter, not just a descriptive reference, so the caller
must resolve and supply it explicitly via `prompt_image` (the same
"caller resolves the mapping, this function doesn't guess it" pattern
`assembly/builder.py`'s `shots_by_candidate_id` parameter already
uses). `mode` defaults to `"image_to_video"` (Runway's more
controllable, more commonly used mode, matching Kling's own default
for a fresh task) but compilation fails closed if that mode is chosen
without a `prompt_image`.

Runway's duration is a discrete choice per model (commonly 4, 6, or 8
seconds -- see models.py's RUNWAY_DURATION_OPTIONS_SECONDS revision
note), not a continuous range up to a max the way Kling's is --
compilation fails closed if the RenderTask's duration_seconds isn't
(within a small tolerance) one of profile.supported_durations_seconds,
rounding up to the nearest supported value rather than silently
truncating a shot to a shorter clip than requested.

`negative_prompt` defaults to RUNWAY_NEGATIVE_PROMPT_BASELINE (this
pipeline's own vocabulary, reused from Kling's), confirmed to be a
real, accepted parameter on Runway's side (see models.py's revision
note -- the first version of this file wrongly assumed it wasn't).
`audio` defaults to the shot's own `requirements.lip_sync_required`:
a shot that needs lip sync needs audio generated with it.
"""
from __future__ import annotations

from ...production.models import Shot
from ...slicer.models import RenderTask
from .errors import RunwayCompilerError
from .ids import generate_runway_package_id
from .models import RUNWAY_NEGATIVE_PROMPT_BASELINE, RunwayPackage, RunwayProfile
from .schema import validate_runway_package_schema

_DURATION_TOLERANCE_SECONDS = 0.05


def _validate_mode(mode: str, prompt_image: str | None, render_task: RenderTask, profile: RunwayProfile) -> None:
    if mode not in profile.supported_modes:
        raise RunwayCompilerError([f"mode {mode!r} requested for render_task {render_task.id!r} is not in this RunwayProfile's supported_modes {list(profile.supported_modes)}"])
    if mode == "image_to_video" and not prompt_image:
        raise RunwayCompilerError([
            f"render_task {render_task.id!r} requested mode 'image_to_video' but no prompt_image was given -- "
            "Runway's real API requires one resolved reference image URL for this mode, and RenderTask."
            "required_assets only carries entity ids, not resolved image paths"
        ])


def _select_duration(render_task: RenderTask, profile: RunwayProfile) -> float:
    candidates = sorted(profile.supported_durations_seconds)
    for candidate in candidates:
        if candidate >= render_task.duration_seconds - _DURATION_TOLERANCE_SECONDS:
            return candidate
    raise RunwayCompilerError([
        f"render_task {render_task.id!r} duration_seconds {render_task.duration_seconds} exceeds the largest "
        f"duration this RunwayProfile supports ({candidates[-1] if candidates else 'none declared'})"
    ])


def _select_ratio(profile: RunwayProfile) -> str:
    if not profile.supported_ratios:
        raise RunwayCompilerError(["RunwayProfile.supported_ratios is empty -- at least one output resolution must be declared"])
    return profile.supported_ratios[0]


def _build_prompt_text(render_task: RenderTask, shot: Shot, mode: str) -> str:
    lines = [
        f"{shot.timing.song_section}: {shot.purpose.narrative_function}, {shot.purpose.editorial_function}.",
        f"Inherited state: {shot.continuity.inherited_state}. Destination state: {shot.continuity.destination_state}.",
        f"Camera motion: {shot.requirements.camera_motion}. Choreography complexity: {shot.requirements.choreography_complexity}.",
        "Preserve character identity, wardrobe, world, props, camera axis, lighting direction, and emotional momentum.",
        "Do not perform any future action beyond this shot's destination state.",
    ]
    if mode == "image_to_video":
        lines.insert(0, "Animate the reference image forward in time; do not redesign its subject, wardrobe, or setting.")
    return " ".join(lines)


def compile_runway_package(
    render_task: RenderTask,
    shot: Shot,
    profile: RunwayProfile,
    mode: str = "image_to_video",
    prompt_image: str | None = None,
    negative_prompt: tuple[str, ...] | None = RUNWAY_NEGATIVE_PROMPT_BASELINE,
    seed: int | None = None,
    audio: bool | None = None,
    package_id: str | None = None,
) -> RunwayPackage:
    if render_task.shot_id != shot.id:
        raise RunwayCompilerError([f"render_task {render_task.id!r} belongs to shot {render_task.shot_id!r}, not {shot.id!r}"])

    _validate_mode(mode, prompt_image, render_task, profile)
    duration_seconds = _select_duration(render_task, profile)
    ratio = _select_ratio(profile)

    package = RunwayPackage(
        id=package_id or generate_runway_package_id(),
        render_task_id=render_task.id,
        shot_id=shot.id,
        mode=mode,
        model=profile.model,
        prompt_text=_build_prompt_text(render_task, shot, mode),
        duration_seconds=duration_seconds,
        ratio=ratio,
        prompt_image=prompt_image,
        negative_prompt=", ".join(negative_prompt) if negative_prompt else None,
        seed=seed,
        audio=audio if audio is not None else shot.requirements.lip_sync_required,
        reference_manifest=render_task.required_assets,
    )

    errors = validate_runway_package_schema(package.to_dict())
    if errors:
        raise RunwayCompilerError(errors)
    return package


def compile_runway_packages(
    render_tasks: tuple[RenderTask, ...],
    shot: Shot,
    profile: RunwayProfile,
    mode: str = "image_to_video",
    prompt_image: str | None = None,
) -> tuple[RunwayPackage, ...]:
    return tuple(
        compile_runway_package(render_task, shot, profile, mode=mode, prompt_image=prompt_image)
        for render_task in render_tasks
    )
