from __future__ import annotations

import json
import unittest
from pathlib import Path

from dreammusicforge.capability_atlas import (
    ShotRequirement,
    evaluate_renderer,
    rank_renderers,
    validate_profile,
)


PROFILE_PATH = (
    Path(__file__).parents[1]
    / "capability_atlas"
    / "profiles"
    / "kling_video_3_omni.json"
)


class CapabilityAtlasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    def test_profile_is_valid(self) -> None:
        self.assertEqual([], validate_profile(self.profile))

    def test_invalid_capability_score_fails(self) -> None:
        profile = json.loads(json.dumps(self.profile))
        profile["capabilities"]["identity"]["score"] = 101
        self.assertTrue(validate_profile(profile))

    def test_duration_over_limit_is_rejected(self) -> None:
        shot = ShotRequirement(
            shot_id="SHOT-001",
            duration_seconds=20,
            required_capabilities={"identity": 70},
            complexity_factors={},
        )
        result = evaluate_renderer(self.profile, shot)
        self.assertFalse(result.accepted)
        self.assertTrue(any("exceeds renderer limit" in item for item in result.failures))

    def test_critical_identity_failure_is_rejected(self) -> None:
        shot = ShotRequirement(
            shot_id="SHOT-002",
            duration_seconds=8,
            required_capabilities={"identity": 95},
            complexity_factors={},
        )
        result = evaluate_renderer(self.profile, shot)
        self.assertFalse(result.accepted)
        self.assertTrue(any(item.startswith("identity") for item in result.failures))

    def test_low_risk_simple_beauty_shot_can_pass(self) -> None:
        shot = ShotRequirement(
            shot_id="SHOT-003",
            duration_seconds=6,
            required_capabilities={"individual_cinematic_quality": 80},
            complexity_factors={},
        )
        result = evaluate_renderer(self.profile, shot)
        self.assertTrue(result.accepted)
        self.assertEqual("LOW", result.risk_band)

    def test_complexity_penalty_reduces_fit(self) -> None:
        simple = ShotRequirement(
            shot_id="SHOT-004",
            duration_seconds=8,
            required_capabilities={"solo_choreography": 70},
            complexity_factors={},
        )
        complex_shot = ShotRequirement(
            shot_id="SHOT-005",
            duration_seconds=8,
            required_capabilities={"solo_choreography": 70},
            complexity_factors={"camera_orbit": 10, "dense_lighting": 8},
        )
        self.assertGreater(
            evaluate_renderer(self.profile, simple).fit_score,
            evaluate_renderer(self.profile, complex_shot).fit_score,
        )

    def test_renderer_ranking_orders_by_fit(self) -> None:
        stronger = json.loads(json.dumps(self.profile))
        stronger["renderer_id"] = "stronger"
        stronger["capabilities"]["identity"]["score"] = 98
        shot = ShotRequirement(
            shot_id="SHOT-006",
            duration_seconds=8,
            required_capabilities={"identity": 90},
            complexity_factors={},
        )
        results = rank_renderers([self.profile, stronger], shot)
        self.assertEqual("stronger", results[0].renderer_id)


if __name__ == "__main__":
    unittest.main()
