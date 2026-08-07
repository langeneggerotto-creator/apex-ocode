from __future__ import annotations

from typing import Any

from .models import ExperienceCheckpoint, ExperienceGraph, Transformation
from .validator import assert_valid_experience_graph


def compile_experience_graph(payload: dict[str, Any]) -> ExperienceGraph:
    transformation_data = payload.get("transformation") or {}
    checkpoints_data = payload.get("checkpoints") or []

    graph = ExperienceGraph(
        version=str(payload.get("version", "0.1")),
        duration_seconds=float(payload["duration_seconds"]),
        transformation=Transformation(
            from_state=str(transformation_data.get("from", "")),
            to_state=str(transformation_data.get("to", "")),
        ),
        checkpoints=tuple(
            ExperienceCheckpoint(
                t_start=float(item["t_start"]),
                t_end=float(item["t_end"]),
                primary_experience=str(item["primary_experience"]),
                intensity=float(item["intensity"]),
                attention_goal=str(item.get("attention_goal", "")),
                memory_goal=str(item.get("memory_goal", "")),
                intended_inference=str(item.get("intended_inference", "")),
                secondary_experiences=tuple(str(v) for v in item.get("secondary_experiences", [])),
                prohibited_inference=tuple(str(v) for v in item.get("prohibited_inference", [])),
                evidence_status=str(item.get("evidence_status", "UNKNOWN")),
            )
            for item in checkpoints_data
        ),
    )
    assert_valid_experience_graph(graph)
    return graph
