from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from dreammusicforge.dmf_ir import (
    compile as dmf_compile,
    parse_project,
    validate,
    validate_schema,
    validate_semantics,
)

EXAMPLE = Path(__file__).parents[2] / "examples" / "begin_again_project.json"


class DMFIRSchemaValidationTests(unittest.TestCase):
    """DMF-IR validation -- required by the delegation contract."""

    def setUp(self):
        self.project = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_valid_project_passes_schema_and_semantics(self):
        result = validate(self.project)
        self.assertTrue(result.valid, result.errors)

    def test_missing_top_level_field_is_rejected(self):
        project = copy.deepcopy(self.project)
        del project["worlds"]
        result = validate_schema(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("missing required top-level field: worlds" in e for e in result.errors))

    def test_missing_nested_required_field_is_rejected(self):
        project = copy.deepcopy(self.project)
        del project["clips"][0]["continuity_mode"]
        result = validate_schema(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("clips[CLIP-001].continuity_mode is required" in e for e in result.errors))

    def test_non_dict_project_is_rejected(self):
        result = validate_schema(["not", "a", "project"])
        self.assertFalse(result.valid)

    def test_schema_version_is_optional(self):
        project = copy.deepcopy(self.project)
        self.assertNotIn("schema_version", project)
        result = validate_schema(project)
        self.assertTrue(result.valid, result.errors)
        parsed = parse_project(project)
        self.assertEqual(parsed.schema_version, "1.0.0")


class DMFIRClipStateInheritanceTests(unittest.TestCase):
    """Clip state inheritance -- required by the delegation contract."""

    def setUp(self):
        self.project = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_state_inheritance_failure(self):
        project = copy.deepcopy(self.project)
        project["clips"][1]["source_state_id"] = "STATE-000"
        result = validate(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("breaks state inheritance" in e for e in result.errors))

    def test_every_clip_imports_exactly_one_source_state(self):
        parsed = parse_project(self.project)
        for clip in parsed.clips:
            self.assertIsInstance(clip.source_state_id, str)
            self.assertTrue(clip.source_state_id)

    def test_source_state_timecode_must_match_clip_start(self):
        project = copy.deepcopy(self.project)
        project["reality_states"][1]["timecode"] = 999
        result = validate(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("does not match clip start" in e or "does not match clip end" in e for e in result.errors))


class DMFIRNewSemanticChecksTests(unittest.TestCase):
    """Checks this IR adds beyond runtime.validate_project -- the actual
    'full' part of replacing the lightweight project structure."""

    def setUp(self):
        self.project = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_first_clip_cannot_require_a_previous_clip(self):
        project = copy.deepcopy(self.project)
        project["clips"][0]["continuity_mode"] = "last_frame_seed"
        result = validate(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("first in the timeline" in e for e in result.errors))

    def test_film_duration_must_match_last_clip_end(self):
        project = copy.deepcopy(self.project)
        project["film"]["duration_seconds"] = 999
        result = validate(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("does not match the last clip's end time" in e for e in result.errors))

    def test_music_timeline_gap_is_rejected(self):
        project = copy.deepcopy(self.project)
        project["music_events"][1]["start"] = 12  # gap between 10 and 12
        result = validate(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("gap or overlap" in e for e in result.errors))

    def test_semantic_event_outside_clip_window_is_rejected(self):
        project = copy.deepcopy(self.project)
        project["semantic_events"][0]["start"] = 50
        project["semantic_events"][0]["end"] = 60
        result = validate(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("does not overlap the clip window" in e for e in result.errors))

    def test_unknown_reference_asset_is_rejected(self):
        project = copy.deepcopy(self.project)
        project["clips"][0]["required_reference_assets"] = ["GHOST-CHARACTER-999"]
        result = validate(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("unknown character/world" in e for e in result.errors))

    def test_bad_pass_threshold_is_rejected(self):
        project = copy.deepcopy(self.project)
        project["verification_contracts"][0]["pass_threshold"] = 1.5
        result = validate(project)
        self.assertFalse(result.valid)
        self.assertTrue(any("pass_threshold must be in (0, 1]" in e for e in result.errors))


class DMFIRProviderNeutralCompilationTests(unittest.TestCase):
    """Kling provider compilation + final-frame handoff -- required by the
    delegation contract, expressed here in provider-neutral terms (the
    Continuity Compiler stage sits before any provider adapter)."""

    def setUp(self):
        self.project = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_compile_rejects_invalid_project(self):
        project = copy.deepcopy(self.project)
        del project["clips"][1]["continuity_mode"]
        with self.assertRaises(ValueError):
            dmf_compile(project)

    def test_compile_orders_clips(self):
        plan = dmf_compile(self.project)
        self.assertEqual([c.clip_id for c in plan.clips], ["CLIP-001", "CLIP-002"])
        self.assertEqual([c.order for c in plan.clips], [1, 2])

    def test_first_clip_has_no_dependency(self):
        plan = dmf_compile(self.project)
        first = plan.clips[0]
        self.assertIsNone(first.depends_on_clip_id)
        self.assertEqual(first.dependency_kind, "reference_assets_only")

    def test_last_frame_seed_handoff_is_provider_neutral(self):
        """Same continuity guarantee runtime.py's test_last_frame_handoff
        checks, expressed without a Kling-specific filename -- a
        verified_end_frame dependency on the correct predecessor clip,
        which any provider compiler can translate into its own asset
        naming convention."""
        plan = dmf_compile(self.project)
        second = plan.clips[1]
        self.assertEqual(second.dependency_kind, "verified_end_frame")
        self.assertEqual(second.depends_on_clip_id, "CLIP-001")

    def test_compiled_clip_resolves_full_objects_not_bare_ids(self):
        plan = dmf_compile(self.project)
        first = plan.clips[0]
        self.assertEqual(first.source_state.id, "STATE-000")
        self.assertEqual(first.destination_state.id, "STATE-010")
        self.assertEqual([e.id for e in first.semantic_events], ["SEM-001"])
        self.assertEqual([e.id for e in first.music_events], ["MUS-001"])
        self.assertEqual(first.verification_contract.id, "VER-001")

    def test_required_reference_ids_are_deduplicated_and_ordered(self):
        project = copy.deepcopy(self.project)
        project["clips"][0]["required_reference_assets"] = ["NOLA-001", "ROOFTOP-01", "NOLA-001"]
        plan = dmf_compile(project)
        self.assertEqual(plan.clips[0].required_reference_ids, ("NOLA-001", "ROOFTOP-01"))

    def test_compiled_plan_carries_no_provider_specific_fields(self):
        """Provider-neutral compiler output check: nothing in the compiled
        plan should name a specific provider (e.g. Kling) or a
        provider-specific asset filename convention."""
        plan = dmf_compile(self.project)
        plan_text = repr(plan)
        for forbidden in ("kling", "Kling", ".mp4", "-VERIFIED-END.png"):
            self.assertNotIn(forbidden, plan_text)


class DMFIRExistingRuntimeStillWorksTests(unittest.TestCase):
    """DMF-IR is additive: runtime.py's existing, already-passing behavior
    must be completely unaffected."""

    def test_runtime_still_validates_and_compiles_the_same_example(self):
        from dreammusicforge.runtime import compile_kling_packages, validate_project

        project = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        result = validate_project(project)
        self.assertTrue(result.valid, result.errors)
        packages = compile_kling_packages(project)
        self.assertEqual(len(packages), 2)
        self.assertEqual(packages[0]["provider"], "kling-video-3-omni")


if __name__ == "__main__":
    unittest.main()
