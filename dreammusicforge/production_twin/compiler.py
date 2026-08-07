from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .models import ProductionTwin, RendererTaskContract, TwinState
from .validator import assert_valid_twin


def compile_renderer_tasks(twin: ProductionTwin) -> tuple[RendererTaskContract, ...]:
    """Compile adjacent Twin states into provider-neutral renderer contracts."""
    assert_valid_twin(twin)
    tasks: list[RendererTaskContract] = []
    for index, (source, dest) in enumerate(zip(twin.states, twin.states[1:]), start=1):
        required = tuple(sorted(set(source.invariants) | set(dest.invariants)))
        permitted = tuple(sorted(set(source.allowed_mutations) | set(dest.allowed_mutations)))
        tasks.append(
            RendererTaskContract(
                task_id=f"{twin.twin_id}-TASK-{index:04d}",
                source_state_id=source.state_id,
                destination_state_id=dest.state_id,
                duration_seconds=dest.start_seconds - source.start_seconds,
                required_invariants=required,
                permitted_changes=permitted,
                performer_id=source.performer.performer_id,
                costume_id=source.performer.costume_id,
                hair_id=source.performer.hair_id,
                world_id=source.world.world_id,
                camera=source.camera,
                lighting=source.lighting,
                music_start_seconds=source.music.time_seconds,
                music_end_seconds=dest.music.time_seconds,
                experience_target=dest.experience,
            )
        )
    return tuple(tasks)


def canonical_twin_payload(twin: ProductionTwin) -> dict:
    assert_valid_twin(twin)
    return twin.to_dict()


def canonical_task_payloads(tasks: Iterable[RendererTaskContract]) -> list[dict]:
    return [asdict(task) for task in tasks]
