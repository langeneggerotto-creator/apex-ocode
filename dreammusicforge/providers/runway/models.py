"""Typed domain model for the Runway provider -- not part of the
original spec's numbered release plan (the spec only ever names Kling
as a provider); added because the user asked to connect Runway as a
second video-generation provider, mirroring providers.kling's
architecture from Release 0.7.

Field shapes here are grounded in Runway's real, documented API (not
invented): the async task-submission pattern
(`POST /v1/image_to_video` / `POST /v1/text_to_video`, then
`GET /v1/tasks/{id}` for `PENDING`/`RUNNING`/`SUCCEEDED`/`FAILED`), a
single required `promptImage` for image-to-video mode, a discrete
`duration` of 5 or 10 seconds (not a continuous range the way Kling's
`max_duration_seconds` is), an explicit output resolution string
instead of a `16:9`/`9:16` ratio keyword (a change from Runway's
earlier API version), and an optional integer `seed`. Sourced from
Runway's public developer docs and third-party API references as of
August 2026 -- not verified by an actual authenticated call to
Runway's API in this session, since no API key was available (see
providers/runway/client.py's module docstring).

Deliberately does NOT copy Kling's `negative_prompt` field: Runway's
public API has no equivalent parameter, and inventing one that's
silently dropped before the real request would misrepresent what's
actually sent. `RunwayPackage.reference_manifest` still carries every
reference asset for evidence/traceability (same discipline as
`KlingPackage.reference_manifest`), separately from `prompt_image`,
which is specifically the one image the real API endpoint accepts.

RUNWAY_MODELS and RUNWAY_RATIOS are illustrative, not exhaustive --
model names and valid resolution strings are genuinely
version-/account-dependent on Runway's side; `RunwayProfile.
supported_models`/`supported_ratios` are the declared, per-deployment
override, same role `KlingProfile.supported_modes` plays for Kling.

Same to_dict()/from_dict() convention as the rest of this repo's domain
models -- frozen dataclasses, not the JSON-Schema-in-a-dict pattern used
elsewhere in this repo's sibling dreammusicforge module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

RUNWAY_MODES = ("text_to_video", "image_to_video")
RUNWAY_DURATION_OPTIONS_SECONDS = (5.0, 10.0)
RUNWAY_MODELS = ("gen3a_turbo", "gen4_turbo", "gen4.5")
RUNWAY_RATIOS = ("1280:720", "720:1280", "1104:832", "832:1104", "960:960")


@dataclass(frozen=True)
class RunwayProfile:
    model: str
    max_duration_seconds: float = 10.0
    supported_modes: tuple[str, ...] = RUNWAY_MODES
    supported_durations_seconds: tuple[float, ...] = RUNWAY_DURATION_OPTIONS_SECONDS
    supported_ratios: tuple[str, ...] = RUNWAY_RATIOS

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "max_duration_seconds": self.max_duration_seconds,
            "supported_modes": list(self.supported_modes),
            "supported_durations_seconds": list(self.supported_durations_seconds),
            "supported_ratios": list(self.supported_ratios),
        }

    @staticmethod
    def from_dict(data: dict) -> "RunwayProfile":
        return RunwayProfile(
            model=data["model"],
            max_duration_seconds=float(data.get("max_duration_seconds", 10.0)),
            supported_modes=tuple(data.get("supported_modes", RUNWAY_MODES)),
            supported_durations_seconds=tuple(data.get("supported_durations_seconds", RUNWAY_DURATION_OPTIONS_SECONDS)),
            supported_ratios=tuple(data.get("supported_ratios", RUNWAY_RATIOS)),
        )


@dataclass(frozen=True)
class RunwayPackage:
    id: str
    render_task_id: str
    shot_id: str
    mode: str
    model: str
    prompt_text: str
    duration_seconds: float
    ratio: str
    prompt_image: str | None = None
    seed: int | None = None
    reference_manifest: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "render_task_id": self.render_task_id,
            "shot_id": self.shot_id,
            "mode": self.mode,
            "model": self.model,
            "prompt_text": self.prompt_text,
            "duration_seconds": self.duration_seconds,
            "ratio": self.ratio,
            "prompt_image": self.prompt_image,
            "seed": self.seed,
            "reference_manifest": list(self.reference_manifest),
        }

    @staticmethod
    def from_dict(data: dict) -> "RunwayPackage":
        return RunwayPackage(
            id=data["id"],
            render_task_id=data["render_task_id"],
            shot_id=data["shot_id"],
            mode=data["mode"],
            model=data["model"],
            prompt_text=data["prompt_text"],
            duration_seconds=float(data["duration_seconds"]),
            ratio=data["ratio"],
            prompt_image=data.get("prompt_image"),
            seed=data.get("seed"),
            reference_manifest=tuple(data.get("reference_manifest", [])),
        )
