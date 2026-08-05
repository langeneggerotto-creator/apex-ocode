from __future__ import annotations

import copy
import unittest

from dreammusicforge.slicer.schema import (
    validate_motion_layer_schema, validate_render_task_schema, validate_slice_result_schema,
    validate_temporal_slice_schema, validate_visual_layer_schema,
)

VALID_TEMPORAL_SLICE = {"id": "SLICE-deadbeef", "index": 0, "start_seconds": 0.0, "end_seconds": 5.0}
VALID_VISUAL_LAYER = {"id": "LAYER-deadbeef", "name": "world_pass"}
VALID_MOTION_LAYER = {"id": "LAYER-11111111", "name": "primary_motion", "camera_motion": "slow_push"}

VALID_RENDER_TASK = {
    "id": "RENDER-deadbeef", "shot_id": "SHOT-deadbeef", "slice_id": "SLICE-deadbeef", "provider": "kling",
    "duration_seconds": 5.0, "required_assets": ["PERFORMER-deadbeef"],
}

VALID_SLICE_RESULT = {
    "shot_id": "SHOT-deadbeef", "strategy": "direct_render", "render_tasks": [VALID_RENDER_TASK],
    "temporal_slices": [VALID_TEMPORAL_SLICE],
}


class TemporalSliceSchemaTests(unittest.TestCase):
    def test_valid_slice_has_no_errors(self):
        self.assertEqual(validate_temporal_slice_schema(VALID_TEMPORAL_SLICE), [])

    def test_start_after_end_is_rejected(self):
        data = dict(VALID_TEMPORAL_SLICE, start_seconds=10.0, end_seconds=5.0)
        errors = validate_temporal_slice_schema(data)
        self.assertTrue(any("start_seconds" in e for e in errors))

    def test_negative_index_is_rejected(self):
        data = dict(VALID_TEMPORAL_SLICE, index=-1)
        errors = validate_temporal_slice_schema(data)
        self.assertTrue(any("index" in e for e in errors))


class VisualLayerSchemaTests(unittest.TestCase):
    def test_valid_layer_has_no_errors(self):
        self.assertEqual(validate_visual_layer_schema(VALID_VISUAL_LAYER), [])

    def test_missing_name_is_reported(self):
        data = copy.deepcopy(VALID_VISUAL_LAYER)
        del data["name"]
        errors = validate_visual_layer_schema(data)
        self.assertTrue(any("name" in e for e in errors))


class MotionLayerSchemaTests(unittest.TestCase):
    def test_valid_layer_has_no_errors(self):
        self.assertEqual(validate_motion_layer_schema(VALID_MOTION_LAYER), [])

    def test_missing_camera_motion_is_reported(self):
        data = copy.deepcopy(VALID_MOTION_LAYER)
        del data["camera_motion"]
        errors = validate_motion_layer_schema(data)
        self.assertTrue(any("camera_motion" in e for e in errors))


class RenderTaskSchemaTests(unittest.TestCase):
    def test_valid_task_has_no_errors(self):
        self.assertEqual(validate_render_task_schema(VALID_RENDER_TASK), [])

    def test_malformed_id_is_rejected(self):
        data = dict(VALID_RENDER_TASK, id="not-a-render-id")
        errors = validate_render_task_schema(data)
        self.assertTrue(any("id" in e for e in errors))

    def test_zero_duration_is_rejected(self):
        data = dict(VALID_RENDER_TASK, duration_seconds=0)
        errors = validate_render_task_schema(data)
        self.assertTrue(any("duration_seconds" in e for e in errors))

    def test_optional_provider_fields_may_be_omitted(self):
        self.assertEqual(validate_render_task_schema(VALID_RENDER_TASK), [])

    def test_empty_optional_provider_field_is_rejected(self):
        data = dict(VALID_RENDER_TASK, mode="")
        errors = validate_render_task_schema(data)
        self.assertTrue(any("mode" in e for e in errors))

    def test_null_optional_provider_field_is_accepted(self):
        data = dict(VALID_RENDER_TASK, mode=None)
        self.assertEqual(validate_render_task_schema(data), [])


class SliceResultSchemaTests(unittest.TestCase):
    def test_valid_direct_render_result_has_no_errors(self):
        self.assertEqual(validate_slice_result_schema(VALID_SLICE_RESULT), [])

    def test_unknown_strategy_is_rejected(self):
        data = dict(VALID_SLICE_RESULT, strategy="teleportation")
        errors = validate_slice_result_schema(data)
        self.assertTrue(any("strategy" in e for e in errors))

    def test_non_external_strategy_without_render_tasks_is_rejected(self):
        data = dict(VALID_SLICE_RESULT, render_tasks=[])
        errors = validate_slice_result_schema(data)
        self.assertTrue(any("must produce at least one render_task" in e for e in errors))

    def test_external_production_required_with_render_tasks_is_rejected(self):
        data = {
            "shot_id": "SHOT-deadbeef", "strategy": "external_production_required",
            "render_tasks": [VALID_RENDER_TASK],
            "fallback_plan": {"reason": "r", "recommended_action": "a"},
        }
        errors = validate_slice_result_schema(data)
        self.assertTrue(any("must not produce any render_tasks" in e for e in errors))

    def test_external_production_required_without_fallback_plan_is_rejected(self):
        data = {"shot_id": "SHOT-deadbeef", "strategy": "external_production_required", "render_tasks": []}
        errors = validate_slice_result_schema(data)
        self.assertTrue(any("fallback_plan" in e for e in errors))

    def test_external_production_required_with_fallback_plan_is_valid(self):
        data = {
            "shot_id": "SHOT-deadbeef", "strategy": "external_production_required", "render_tasks": [],
            "fallback_plan": {"reason": "r", "recommended_action": "a"},
        }
        self.assertEqual(validate_slice_result_schema(data), [])


if __name__ == "__main__":
    unittest.main()
