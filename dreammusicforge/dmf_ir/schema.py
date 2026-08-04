"""DMF-IR v1 schema contract.

This is the canonical, provider-neutral shape every future compiler (music,
continuity, cinematography, editing, verification, provider adapters) reads
from. It formalizes -- without changing -- the project shape already proven
by dreammusicforge/runtime.py and dreammusicforge/examples/begin_again_project.json:
this module adds structure and stricter checking on top of that shape, it
does not invent a new one.

Expressed as a plain, dependency-free Python dict in JSON-Schema-like shape
(no `jsonschema` package required or assumed) so it stays inspectable and
diffable as data, consistent with the "Use JSON schemas" / "Fail closed"
coding rules. validator.py is the executable counterpart: it walks this same
structure by hand rather than relying on an external schema-validation
library.
"""
from __future__ import annotations

DMF_IR_SCHEMA_VERSION = "1.0.0"

# schema_version is optional on a project for backward compatibility with
# begin_again_project.json, which predates this module and carries no such
# field. A project without one is treated as DMF_IR_SCHEMA_VERSION.
DMF_IR_SCHEMA: dict = {
    "$id": "dreammusicforge/dmf_ir/schema.py:DMF_IR_SCHEMA",
    "schema_version": DMF_IR_SCHEMA_VERSION,
    "type": "object",
    "required": [
        "film", "characters", "worlds", "music_events", "semantic_events",
        "reality_states", "clips", "verification_contracts",
    ],
    "properties": {
        "schema_version": {"type": "string", "optional": True},
        "film": {
            "type": "object",
            "required": ["id", "title", "duration_seconds", "aspect_ratio", "frame_rate", "style_identity"],
        },
        "characters": {
            "type": "array",
            "items": {"type": "object", "required": ["id", "identity_locked", "wardrobe_id"]},
        },
        "worlds": {
            "type": "array",
            "items": {"type": "object", "required": ["id", "persistent"]},
        },
        "music_events": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "object", "required": ["id", "start", "end", "section"]},
        },
        "semantic_events": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "object", "required": ["id", "start", "end", "meaning"]},
        },
        "reality_states": {
            "type": "array",
            "minItems": 1,
            "description": "id and timecode are required; everything else (notebook, emotion, ...) is free-form world/character state and deliberately not schema-constrained -- reality_states describe whatever the story needs.",
            "items": {"type": "object", "required": ["id", "timecode"]},
        },
        "clips": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "id", "start", "end", "source_state_id", "destination_state_id",
                    "semantic_event_ids", "music_event_ids", "primary_action",
                    "secondary_actions", "maximum_actions", "continuity_mode",
                    "required_reference_assets", "verification_contract_id",
                ],
            },
        },
        "verification_contracts": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "object", "required": ["id", "pass_threshold", "reject_if"]},
        },
    },
}

# Mirrors runtime.CONTINUITY_MODES exactly -- this module does not introduce
# a competing set of mode names. Each mode is annotated with the kind of
# cross-clip dependency it implies, in provider-neutral terms (compiler.py
# uses this, not "kling-video-3-omni"-shaped asset filenames).
CONTINUITY_MODES = {
    "video_extension": "full_video",
    "last_frame_seed": "verified_end_frame",
    "first_last_frame": "verified_end_frame",
    "character_reference": "reference_assets_only",
    "world_reference": "reference_assets_only",
    "text_only_fallback": "none",
}

# Modes in this set are only valid on a clip that has a predecessor --
# runtime.py silently no-ops this case rather than rejecting it; DMF-IR
# validates it explicitly (fail closed).
PREVIOUS_CLIP_REQUIRED_MODES = {
    mode for mode, kind in CONTINUITY_MODES.items() if kind in ("full_video", "verified_end_frame")
}
