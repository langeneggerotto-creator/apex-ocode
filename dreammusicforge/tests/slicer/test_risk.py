from __future__ import annotations

import unittest

from dreammusicforge.capability_atlas.builder import build_capability, build_capability_profile
from dreammusicforge.capability_atlas.scoring import evaluate_shot_fit
from dreammusicforge.production.models import Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming
from dreammusicforge.slicer.risk import compute_risk_factors


def _shot(character_count=1, choreography_complexity="low", camera_motion="slow_push", lip_sync_required=False, duration=6.0, acceptance=None):
    return Shot(
        id="SHOT-deadbeef", sequence_id="SEQ-deadbeef",
        timing=ShotTiming(start_seconds=0.0, end_seconds=duration, song_section="verse_1"),
        purpose=ShotPurpose(semantic_event_id="SEM-deadbeef", narrative_function="n", editorial_function="e"),
        requirements=ShotRequirements(
            performer_id="PERFORMER-deadbeef", costume_id="COSTUME-deadbeef", world_id="WORLD-deadbeef",
            lip_sync_required=lip_sync_required, choreography_complexity=choreography_complexity,
            camera_motion=camera_motion, character_count=character_count,
        ),
        continuity=ShotContinuity(inherited_state="a", permitted_mutations=(), destination_state="b"),
        acceptance=acceptance if acceptance is not None else {"identity": 95.0},
    )


class ComputeRiskFactorsTests(unittest.TestCase):
    def test_duration_risk_is_ratio_of_max(self):
        shot = _shot(duration=6.0)
        profile = build_capability_profile(provider="kling", max_duration_seconds=12.0, max_character_count=3, supported_camera_motions=("slow_push",))
        fit = evaluate_shot_fit(shot, profile)
        risk = compute_risk_factors(shot, profile, fit)
        self.assertEqual(risk.duration, 50.0)

    def test_character_count_risk_is_ratio_of_max(self):
        shot = _shot(character_count=2)
        profile = build_capability_profile(provider="kling", max_duration_seconds=12.0, max_character_count=4, supported_camera_motions=("slow_push",))
        fit = evaluate_shot_fit(shot, profile)
        risk = compute_risk_factors(shot, profile, fit)
        self.assertEqual(risk.character_count, 50.0)

    def test_low_choreography_maps_to_low_risk(self):
        shot = _shot(choreography_complexity="low")
        profile = build_capability_profile(provider="kling", max_duration_seconds=12.0, max_character_count=3, supported_camera_motions=("slow_push",))
        fit = evaluate_shot_fit(shot, profile)
        risk = compute_risk_factors(shot, profile, fit)
        self.assertEqual(risk.choreography_complexity, 20.0)

    def test_unknown_choreography_label_falls_back_to_default(self):
        shot = _shot(choreography_complexity="chaotic")
        profile = build_capability_profile(provider="kling", max_duration_seconds=12.0, max_character_count=3, supported_camera_motions=("slow_push",))
        fit = evaluate_shot_fit(shot, profile)
        risk = compute_risk_factors(shot, profile, fit)
        self.assertEqual(risk.choreography_complexity, 50.0)

    def test_supported_camera_motion_has_zero_risk(self):
        shot = _shot(camera_motion="slow_push")
        profile = build_capability_profile(provider="kling", max_duration_seconds=12.0, max_character_count=3, supported_camera_motions=("slow_push",))
        fit = evaluate_shot_fit(shot, profile)
        risk = compute_risk_factors(shot, profile, fit)
        self.assertEqual(risk.camera_motion, 0.0)

    def test_lip_sync_not_required_has_zero_risk(self):
        shot = _shot(lip_sync_required=False)
        profile = build_capability_profile(provider="kling", max_duration_seconds=12.0, max_character_count=3, supported_camera_motions=("slow_push",))
        fit = evaluate_shot_fit(shot, profile)
        risk = compute_risk_factors(shot, profile, fit)
        self.assertEqual(risk.lip_sync, 0.0)

    def test_lip_sync_required_with_verified_capability_has_zero_risk(self):
        shot = _shot(lip_sync_required=True, acceptance={"identity": 95.0, "lip_sync": 90.0})
        profile = build_capability_profile(
            provider="kling", max_duration_seconds=12.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("lip_sync", "verified"),),
        )
        fit = evaluate_shot_fit(shot, profile)
        risk = compute_risk_factors(shot, profile, fit)
        self.assertEqual(risk.lip_sync, 0.0)

    def test_continuity_dependency_reflects_predecessor_flag(self):
        shot = _shot()
        profile = build_capability_profile(provider="kling", max_duration_seconds=12.0, max_character_count=3, supported_camera_motions=("slow_push",))
        fit = evaluate_shot_fit(shot, profile)
        without_predecessor = compute_risk_factors(shot, profile, fit, has_predecessor=False)
        with_predecessor = compute_risk_factors(shot, profile, fit, has_predecessor=True)
        self.assertLess(without_predecessor.continuity_dependency, with_predecessor.continuity_dependency)

    def test_provider_support_risk_is_inverse_of_fit_score(self):
        shot = _shot(acceptance={"identity": 95.0})
        profile = build_capability_profile(
            provider="kling", max_duration_seconds=12.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("identity", "verified"),),
        )
        fit = evaluate_shot_fit(shot, profile)
        risk = compute_risk_factors(shot, profile, fit)
        self.assertEqual(risk.provider_support, 100.0 - fit.overall_score)

    def test_disqualified_fit_maxes_out_provider_support_risk(self):
        shot = _shot(duration=20.0)
        profile = build_capability_profile(provider="kling", max_duration_seconds=6.0, max_character_count=3, supported_camera_motions=("slow_push",))
        fit = evaluate_shot_fit(shot, profile)
        risk = compute_risk_factors(shot, profile, fit)
        self.assertEqual(risk.provider_support, 100.0)

    def test_unassessed_risk_factors_stay_none(self):
        shot = _shot()
        profile = build_capability_profile(provider="kling", max_duration_seconds=12.0, max_character_count=3, supported_camera_motions=("slow_push",))
        fit = evaluate_shot_fit(shot, profile)
        risk = compute_risk_factors(shot, profile, fit)
        self.assertIsNone(risk.prop_interaction)
        self.assertIsNone(risk.facial_performance)
        self.assertIsNone(risk.hand_complexity)
        self.assertIsNone(risk.lighting_change)
        self.assertIsNone(risk.transition_complexity)


if __name__ == "__main__":
    unittest.main()
