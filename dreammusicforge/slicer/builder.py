"""slice_shot(): the top-level orchestration that turns a Shot and its
ProviderFitReport into a validated SliceResult -- this release's
acceptance test from spec section 19: "complex shot becomes executable
render tasks."

Temporal slicing, visual layers, and motion layers only get built for
strategies that actually render something; `external_production_required`
produces zero render tasks and a FallbackPlan instead, quoting spec
section 7.4's own recommendation for that case.
"""
from __future__ import annotations

import math

from ..capability_atlas.models import ProviderFitReport, RendererCapabilityProfile
from ..production.models import Shot
from .errors import SlicerValidationError
from .ids import generate_layer_id, generate_render_task_id, generate_slice_id
from .models import EXPECTED_RENDER_OUTPUTS, FallbackPlan, MotionLayer, RenderTask, SliceResult, TemporalSlice, VisualLayer
from .schema import validate_slice_result_schema
from .strategy import select_strategy

_EXTERNAL_PRODUCTION_ACTION = "a conventional or dedicated specialist tool is more reliable"


def _required_assets(shot: Shot) -> tuple[str, ...]:
    return (shot.requirements.performer_id, shot.requirements.costume_id, shot.requirements.world_id)


def _single_span_slices(shot: Shot) -> tuple[TemporalSlice, ...]:
    return (TemporalSlice(id=generate_slice_id(), index=0, start_seconds=shot.timing.start_seconds, end_seconds=shot.timing.end_seconds),)


def _continuation_slices(shot: Shot, max_duration_seconds: float) -> tuple[TemporalSlice, ...]:
    total_duration = shot.timing.end_seconds - shot.timing.start_seconds
    chunk_count = math.ceil(total_duration / max_duration_seconds)
    chunk_duration = total_duration / chunk_count
    slices = []
    for index in range(chunk_count):
        start = shot.timing.start_seconds + index * chunk_duration
        end = shot.timing.start_seconds + total_duration if index == chunk_count - 1 else start + chunk_duration
        slices.append(TemporalSlice(id=generate_slice_id(), index=index, start_seconds=start, end_seconds=end))
    return tuple(slices)


def _visual_layers(shot: Shot) -> tuple[VisualLayer, ...]:
    layers = [
        VisualLayer(id=generate_layer_id(), name="world_pass"),
        VisualLayer(id=generate_layer_id(), name="performer_pass"),
    ]
    if shot.requirements.lip_sync_required:
        layers.append(VisualLayer(id=generate_layer_id(), name="lip_sync_pass"))
    return tuple(layers)


def _motion_layers(shot: Shot) -> tuple[MotionLayer, ...]:
    return (MotionLayer(id=generate_layer_id(), name="primary_motion", camera_motion=shot.requirements.camera_motion),)


def slice_shot(
    shot: Shot,
    fit_report: ProviderFitReport,
    profiles_by_provider: dict[str, RendererCapabilityProfile],
    has_predecessor: bool = False,
) -> SliceResult:
    decision = select_strategy(shot, fit_report, profiles_by_provider, has_predecessor)
    required_assets = _required_assets(shot)
    critical_checks = tuple(shot.acceptance)

    temporal_slices: tuple[TemporalSlice, ...] = ()
    visual_layers: tuple[VisualLayer, ...] = ()
    motion_layers: tuple[MotionLayer, ...] = ()
    render_tasks: tuple[RenderTask, ...] = ()
    fallback_plan: FallbackPlan | None = None

    if decision.strategy == "direct_render":
        temporal_slices = _single_span_slices(shot)
        motion_layers = _motion_layers(shot)
        render_tasks = (
            RenderTask(
                id=generate_render_task_id(), shot_id=shot.id, slice_id=temporal_slices[0].id,
                provider=decision.provider, duration_seconds=shot.timing.end_seconds - shot.timing.start_seconds,
                required_assets=required_assets, expected_outputs=EXPECTED_RENDER_OUTPUTS, critical_checks=critical_checks,
            ),
        )

    elif decision.strategy == "layered_compositing":
        temporal_slices = _single_span_slices(shot)
        visual_layers = _visual_layers(shot)
        motion_layers = _motion_layers(shot)
        render_tasks = tuple(
            RenderTask(
                id=generate_render_task_id(), shot_id=shot.id, slice_id=layer.id,
                provider=decision.provider, duration_seconds=shot.timing.end_seconds - shot.timing.start_seconds,
                required_assets=required_assets, expected_outputs=EXPECTED_RENDER_OUTPUTS, critical_checks=critical_checks,
            )
            for layer in visual_layers
        )

    elif decision.strategy == "controlled_continuation":
        profile = profiles_by_provider[decision.provider]
        temporal_slices = _continuation_slices(shot, profile.max_duration_seconds)
        motion_layers = _motion_layers(shot)
        tasks = []
        previous_task_id: str | None = None
        for temporal_slice in temporal_slices:
            assets = required_assets if previous_task_id is None else required_assets + (f"{previous_task_id}.mp4",)
            task = RenderTask(
                id=generate_render_task_id(), shot_id=shot.id, slice_id=temporal_slice.id,
                provider=decision.provider, duration_seconds=temporal_slice.end_seconds - temporal_slice.start_seconds,
                required_assets=assets, expected_outputs=EXPECTED_RENDER_OUTPUTS, critical_checks=critical_checks,
            )
            tasks.append(task)
            previous_task_id = task.id
        render_tasks = tuple(tasks)

    else:  # external_production_required
        fallback_plan = FallbackPlan(
            reason="; ".join(decision.reasons),
            recommended_action=_EXTERNAL_PRODUCTION_ACTION,
        )

    result = SliceResult(
        shot_id=shot.id, strategy=decision.strategy, provider=decision.provider, reasons=decision.reasons,
        risk_factors=decision.risk_factors, temporal_slices=temporal_slices, visual_layers=visual_layers,
        motion_layers=motion_layers, render_tasks=render_tasks, fallback_plan=fallback_plan,
    )

    errors = validate_slice_result_schema(result.to_dict())
    if errors:
        raise SlicerValidationError(errors)
    return result
