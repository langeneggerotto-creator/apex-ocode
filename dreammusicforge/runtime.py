"""Governed DreamMusicForge clip and Kling provider compiler baseline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CONTINUITY_MODES = {
    "video_extension",
    "last_frame_seed",
    "first_last_frame",
    "character_reference",
    "world_reference",
    "text_only_fallback",
}


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]


def _index(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items if "id" in item}


def validate_project(project: dict[str, Any], max_clip_seconds: float = 15.0) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        "film", "characters", "worlds", "music_events", "semantic_events",
        "reality_states", "clips", "verification_contracts",
    ]
    for field in required:
        if field not in project:
            errors.append(f"Missing top-level field: {field}")
    if errors:
        return ValidationResult(False, errors, warnings)

    states = _index(project["reality_states"])
    semantics = _index(project["semantic_events"])
    music = _index(project["music_events"])
    checks = _index(project["verification_contracts"])
    clips = sorted(project["clips"], key=lambda item: float(item["start"]))
    previous_end = 0.0
    previous_destination: str | None = None

    for clip in clips:
        clip_id = clip["id"]
        start = float(clip["start"])
        end = float(clip["end"])
        duration = end - start
        if start < previous_end:
            errors.append(f"{clip_id} overlaps previous clip")
        if duration <= 0:
            errors.append(f"{clip_id} has invalid duration")
        if duration > max_clip_seconds:
            errors.append(f"{clip_id} exceeds provider duration limit")
        source = clip.get("source_state_id")
        destination = clip.get("destination_state_id")
        if source not in states:
            errors.append(f"{clip_id} missing source state {source}")
        if destination not in states:
            errors.append(f"{clip_id} missing destination state {destination}")
        if previous_destination and source != previous_destination:
            errors.append(f"{clip_id} breaks state inheritance")
        for event_id in clip.get("semantic_event_ids", []):
            if event_id not in semantics:
                errors.append(f"{clip_id} missing semantic event {event_id}")
        for event_id in clip.get("music_event_ids", []):
            if event_id not in music:
                errors.append(f"{clip_id} missing music event {event_id}")
        if clip.get("verification_contract_id") not in checks:
            errors.append(f"{clip_id} missing verification contract")
        if clip.get("continuity_mode") not in CONTINUITY_MODES:
            errors.append(f"{clip_id} uses unsupported continuity mode")
        total_actions = 1 + len(clip.get("secondary_actions", []))
        if total_actions > int(clip.get("maximum_actions", 1)):
            errors.append(f"{clip_id} exceeds maximum action count")
        previous_end = end
        previous_destination = destination

    return ValidationResult(not errors, errors, warnings)


def compile_kling_packages(project: dict[str, Any]) -> list[dict[str, Any]]:
    validation = validate_project(project)
    if not validation.valid:
        raise ValueError("Invalid project:\n- " + "\n- ".join(validation.errors))

    states = _index(project["reality_states"])
    semantics = _index(project["semantic_events"])
    music = _index(project["music_events"])
    verifications = _index(project["verification_contracts"])
    clips = sorted(project["clips"], key=lambda item: float(item["start"]))
    packages: list[dict[str, Any]] = []

    for index, clip in enumerate(clips):
        previous = clips[index - 1]["id"] if index else None
        mode = clip["continuity_mode"]
        assets = list(clip.get("required_reference_assets", []))
        if mode == "last_frame_seed" and previous:
            assets.append(f"{previous}-VERIFIED-END.png")
        if mode == "video_extension" and previous:
            assets.append(f"{previous}.mp4")

        semantic_text = "; ".join(
            str(semantics[event_id].get("meaning", event_id))
            for event_id in clip.get("semantic_event_ids", [])
        )
        music_text = "; ".join(
            f"{event_id} {music[event_id].get('start')}–{music[event_id].get('end')}s"
            for event_id in clip.get("music_event_ids", [])
        )
        prompt = "\n".join([
            f"Create {float(clip['end']) - float(clip['start']):.1f} seconds of cinematic video.",
            f"Continuity mode: {mode}.",
            "Do not rely on memory from prior generations.",
            "Treat supplied frames, videos, and Elements as binding references.",
            f"Source state: {states[clip['source_state_id']]}",
            f"Perform exactly one dominant action: {clip['primary_action']}.",
            "Do not perform any future action.",
            f"Destination state: {states[clip['destination_state_id']]}",
            f"Semantic objective: {semantic_text}.",
            f"Assigned music interval: {music_text}.",
            "The song is the master clock; continue its phrase and energy without reset.",
            "Preserve character identity, wardrobe, world, props, camera axis, lighting direction, and emotional momentum.",
            "Use natural body mechanics and end on a stable frame suitable for the next clip.",
        ]) + "\n"

        packages.append({
            "clip_id": clip["id"],
            "provider": "kling-video-3-omni",
            "mode": mode,
            "duration_seconds": float(clip["end"]) - float(clip["start"]),
            "required_assets": sorted(set(assets)),
            "prompt": prompt,
            "negative_prompt": [
                "identity drift", "wardrobe redesign", "world redesign",
                "prop mutation", "camera reset", "lighting reset", "time jump",
                "extra action", "premature future action", "music restart",
            ],
            "verification": verifications[clip["verification_contract_id"]],
            "must_export": [f"{clip['id']}.mp4", f"{clip['id']}-VERIFIED-END.png"],
        })
    return packages
