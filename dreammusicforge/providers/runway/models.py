"""Typed domain model for the Runway provider -- not part of the
original spec's numbered release plan (the spec only ever names Kling
as a provider); added because the user asked to connect Runway as a
second video-generation provider, mirroring providers.kling's
architecture from Release 0.7.

**Revision note, corrected after this addition first shipped:** the
first version of this file was grounded only in web-search summaries
of Runway's docs (which this environment's egress proxy blocks direct
access to) and got a real detail wrong -- it claimed Runway's API has
no `negative_prompt` parameter. That was outdated/incorrect. This
version is grounded in the actual, installed `runwayml` PyPI SDK
(`pip install runwayml`, verified installable and importable in this
environment), introspected directly rather than summarized secondhand:
`RUNWAY_MODELS` is the real model list `runwayml.resources.
image_to_video.ImageToVideoResource.create()`'s type signature
declares; `negative_prompt`, `audio`, and `seed` are all real
parameters on both `image_to_video.create()` and `text_to_video.
create()`; task status values (including `THROTTLED` and `CANCELLED`,
which the earlier version missed) come from `runwayml.types.
task_retrieve_response`'s real `Literal` status fields. This is a
stronger form of verification than the first pass, but still not the
strongest: no call has actually been made against Runway's live API in
this session (see client.py's module docstring for why).

`ratio` is genuinely model-dependent -- the real SDK's `create()` type
signature has a different `Literal[...]` set of valid ratio strings
*per model*, some with dozens of options. Rather than hardcode that
whole matrix (which would also go stale the moment Runway adds a
model), `RunwayProfile.supported_ratios` stays the declared,
per-deployment override this file already used -- `RUNWAY_RATIOS`
below is illustrative only, a small, safe common subset actually seen
across multiple models' signatures.

`RunwayPackage.reference_manifest` still carries every reference asset
for evidence/traceability (same discipline as `KlingPackage.
reference_manifest`), separately from `prompt_image`, which is
specifically the one resolved image URL/URI the real API parameter
accepts.

Same to_dict()/from_dict() convention as the rest of this repo's domain
models -- frozen dataclasses, not the JSON-Schema-in-a-dict pattern used
elsewhere in this repo's sibling dreammusicforge module.
"""
from __future__ import annotations

from dataclasses import dataclass, field

RUNWAY_MODES = ("text_to_video", "image_to_video")
RUNWAY_TASK_STATUSES = ("PENDING", "THROTTLED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED")
# The installed SDK types `duration` as `int | Literal[4, 6, 8]` -- an int is
# accepted, but 4/6/8 are the values actually offered across models as of
# this check. Like RUNWAY_RATIOS, this is illustrative, not exhaustive:
# RunwayProfile.supported_durations_seconds is the real per-deployment override.
RUNWAY_DURATION_OPTIONS_SECONDS = (4.0, 6.0, 8.0)
RUNWAY_MODELS = (
    "gen4.5", "gen4_turbo", "veo3.1", "veo3.1_fast", "hailuo3", "happyhorse_1_0",
    "seedance2", "seedance2_fast", "seedance2_mini", "seedance2_5", "gemini_omni_flash", "grok_imagine_1_5",
)
RUNWAY_RATIOS = ("1280:720", "720:1280", "1104:832", "832:1104", "960:960")
# This pipeline's own default negative-prompt vocabulary for Runway --
# not a Runway requirement, just this repository's own choice, reusing
# providers.kling's KLING_NEGATIVE_PROMPT_BASELINE verbatim now that
# negative_prompt is confirmed to be a real, supported parameter on
# Runway's side too. Duplicated rather than imported cross-package,
# same "each provider owns its own literal constants" convention every
# provider-specific ffmpeg wrapper in this repository already follows.
RUNWAY_NEGATIVE_PROMPT_BASELINE = (
    "identity drift", "wardrobe redesign", "world redesign", "prop mutation", "camera reset",
    "lighting reset", "time jump", "extra action", "premature future action", "music restart",
)


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
    negative_prompt: str | None = None
    seed: int | None = None
    audio: bool = False
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
            "negative_prompt": self.negative_prompt,
            "seed": self.seed,
            "audio": self.audio,
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
            negative_prompt=data.get("negative_prompt"),
            seed=data.get("seed"),
            audio=bool(data.get("audio", False)),
            reference_manifest=tuple(data.get("reference_manifest", [])),
        )
