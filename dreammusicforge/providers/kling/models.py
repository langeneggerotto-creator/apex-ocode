"""Typed domain model for Release 0.7 -- "each task produces an
operator-usable Kling package" (spec section 19's acceptance test for
this release).

KLING_MODES reuses this same repository's pre-spec `runtime.py`
CONTINUITY_MODES vocabulary (`video_extension`, `image_to_video` derived
from its `last_frame_seed`/direct-generation distinction) rather than
inventing a new one -- the spec names "mode selection" as a deliverable
(section 19) and shows `mode: image_to_video` in section 6.9's
`render_task` example, but gives no closed list of every Kling mode.
`text_to_video` and `start_end_frame` are added because they're standard
Kling capability names widely documented outside this spec; if that
turns out wrong for a specific Kling API version, `KlingProfile.
supported_modes` is exactly the declared, per-deployment override this
model provides for that.

Same to_dict()/from_dict() convention as the rest of this repo's domain
models -- frozen dataclasses, not the JSON-Schema-in-a-dict pattern used
elsewhere in this repo's sibling dreammusicforge module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

KLING_MODES = ("text_to_video", "image_to_video", "start_end_frame", "video_extension")

KLING_NEGATIVE_PROMPT_BASELINE = (
    "identity drift", "wardrobe redesign", "world redesign", "prop mutation", "camera reset",
    "lighting reset", "time jump", "extra action", "premature future action", "music restart",
)


@dataclass(frozen=True)
class KlingProfile:
    max_duration_seconds: float
    supported_modes: tuple[str, ...] = KLING_MODES

    def to_dict(self) -> dict:
        return {"max_duration_seconds": self.max_duration_seconds, "supported_modes": list(self.supported_modes)}

    @staticmethod
    def from_dict(data: dict) -> "KlingProfile":
        return KlingProfile(
            max_duration_seconds=float(data["max_duration_seconds"]),
            supported_modes=tuple(data.get("supported_modes", KLING_MODES)),
        )


@dataclass(frozen=True)
class KlingPackage:
    id: str
    render_task_id: str
    shot_id: str
    mode: str
    duration_seconds: float
    duration_limit_seconds: float
    prompt: str
    negative_prompt: tuple[str, ...]
    reference_manifest: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "render_task_id": self.render_task_id,
            "shot_id": self.shot_id,
            "mode": self.mode,
            "duration_seconds": self.duration_seconds,
            "duration_limit_seconds": self.duration_limit_seconds,
            "prompt": self.prompt,
            "negative_prompt": list(self.negative_prompt),
            "reference_manifest": list(self.reference_manifest),
        }

    @staticmethod
    def from_dict(data: dict) -> "KlingPackage":
        return KlingPackage(
            id=data["id"],
            render_task_id=data["render_task_id"],
            shot_id=data["shot_id"],
            mode=data["mode"],
            duration_seconds=float(data["duration_seconds"]),
            duration_limit_seconds=float(data["duration_limit_seconds"]),
            prompt=data["prompt"],
            negative_prompt=tuple(data.get("negative_prompt", [])),
            reference_manifest=tuple(data.get("reference_manifest", [])),
        )
