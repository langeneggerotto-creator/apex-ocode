from __future__ import annotations

import unittest

from dreammusicforge.slicer.models import (
    FallbackPlan, MotionLayer, RenderTask, RiskFactors, SliceResult, TemporalSlice, VisualLayer,
)

RISK_FACTORS_DATA = {
    "duration": 80.0, "character_count": 62.5, "identity_precision": 0.0, "costume_precision": 100.0,
    "world_precision": 100.0, "choreography_complexity": 80.0, "camera_motion": 0.0, "lip_sync": 20.0,
    "continuity_dependency": 20.0, "provider_support": 10.0, "prop_interaction": None,
    "facial_performance": None, "hand_complexity": None, "lighting_change": None, "transition_complexity": None,
}

TEMPORAL_SLICE_DATA = {"id": "SLICE-deadbeef", "index": 0, "start_seconds": 0.0, "end_seconds": 5.0}
VISUAL_LAYER_DATA = {"id": "LAYER-deadbeef", "name": "world_pass"}
MOTION_LAYER_DATA = {"id": "LAYER-11111111", "name": "primary_motion", "camera_motion": "slow_push"}

RENDER_TASK_DATA = {
    "id": "RENDER-deadbeef", "shot_id": "SHOT-deadbeef", "slice_id": "SLICE-deadbeef", "provider": "kling",
    "duration_seconds": 5.0, "required_assets": ["PERFORMER-deadbeef"], "expected_outputs": ["candidate_video", "final_frame"],
    "critical_checks": ["identity"], "mode": None, "prompt_file": None, "negative_prompt_file": None,
}

SLICE_RESULT_DATA = {
    "shot_id": "SHOT-deadbeef", "strategy": "direct_render", "provider": "kling", "reasons": ["fits"],
    "risk_factors": RISK_FACTORS_DATA, "temporal_slices": [TEMPORAL_SLICE_DATA], "visual_layers": [],
    "motion_layers": [MOTION_LAYER_DATA], "render_tasks": [RENDER_TASK_DATA], "fallback_plan": None,
}


class RiskFactorsRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        risk = RiskFactors.from_dict(RISK_FACTORS_DATA)
        self.assertEqual(risk.to_dict(), RISK_FACTORS_DATA)

    def test_unassessed_factors_default_to_none(self):
        risk = RiskFactors.from_dict(RISK_FACTORS_DATA)
        self.assertIsNone(risk.prop_interaction)
        self.assertIsNone(risk.facial_performance)


class TemporalSliceRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        temporal_slice = TemporalSlice.from_dict(TEMPORAL_SLICE_DATA)
        self.assertEqual(temporal_slice.to_dict(), TEMPORAL_SLICE_DATA)


class VisualLayerRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        layer = VisualLayer.from_dict(VISUAL_LAYER_DATA)
        self.assertEqual(layer.to_dict(), VISUAL_LAYER_DATA)


class MotionLayerRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        layer = MotionLayer.from_dict(MOTION_LAYER_DATA)
        self.assertEqual(layer.to_dict(), MOTION_LAYER_DATA)


class RenderTaskRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        task = RenderTask.from_dict(RENDER_TASK_DATA)
        self.assertEqual(task.to_dict(), RENDER_TASK_DATA)

    def test_expected_outputs_defaults_when_missing(self):
        data = {k: v for k, v in RENDER_TASK_DATA.items() if k != "expected_outputs"}
        task = RenderTask.from_dict(data)
        self.assertEqual(task.expected_outputs, ("candidate_video", "final_frame"))

    def test_optional_provider_fields_default_to_none(self):
        data = {k: v for k, v in RENDER_TASK_DATA.items() if k not in ("mode", "prompt_file", "negative_prompt_file")}
        task = RenderTask.from_dict(data)
        self.assertIsNone(task.mode)
        self.assertIsNone(task.prompt_file)
        self.assertIsNone(task.negative_prompt_file)

    def test_render_task_is_frozen(self):
        task = RenderTask.from_dict(RENDER_TASK_DATA)
        with self.assertRaises(Exception):
            task.provider = "veo"  # type: ignore[misc]


class FallbackPlanRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        data = {"reason": "no provider qualified", "recommended_action": "use a specialist tool"}
        plan = FallbackPlan.from_dict(data)
        self.assertEqual(plan.to_dict(), data)


class SliceResultRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        result = SliceResult.from_dict(SLICE_RESULT_DATA)
        self.assertEqual(result.to_dict(), SLICE_RESULT_DATA)

    def test_none_risk_factors_and_fallback_plan_round_trip(self):
        data = dict(SLICE_RESULT_DATA, risk_factors=None, fallback_plan=None)
        result = SliceResult.from_dict(data)
        self.assertIsNone(result.risk_factors)
        self.assertIsNone(result.fallback_plan)
        self.assertEqual(result.to_dict()["risk_factors"], None)


if __name__ == "__main__":
    unittest.main()
