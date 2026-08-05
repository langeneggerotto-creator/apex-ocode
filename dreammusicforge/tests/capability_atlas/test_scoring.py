from __future__ import annotations

import unittest

from dreammusicforge.capability_atlas.builder import build_capability, build_capability_profile
from dreammusicforge.capability_atlas.scoring import (
    evaluate_shot_fit, rank_providers_for_shot, score_capability_status,
)
from dreammusicforge.production.models import Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming


def _shot(
    lip_sync_required=True, camera_motion="slow_push", character_count=1,
    start_seconds=42.0, end_seconds=48.5, acceptance=None,
):
    return Shot(
        id="SHOT-deadbeef",
        sequence_id="SEQ-deadbeef",
        timing=ShotTiming(start_seconds=start_seconds, end_seconds=end_seconds, song_section="chorus_1"),
        purpose=ShotPurpose(semantic_event_id="SEM-deadbeef", narrative_function="declaration", editorial_function="hero"),
        requirements=ShotRequirements(
            performer_id="PERFORMER-deadbeef", costume_id="COSTUME-deadbeef", world_id="WORLD-deadbeef",
            lip_sync_required=lip_sync_required, choreography_complexity="medium",
            camera_motion=camera_motion, character_count=character_count,
        ),
        continuity=ShotContinuity(inherited_state="concealed", permitted_mutations=(), destination_state="revealed"),
        acceptance=acceptance if acceptance is not None else {"identity": 95.0, "lip_sync": 90.0},
    )


class ScoreCapabilityStatusTests(unittest.TestCase):
    def test_verified_scores_highest(self):
        self.assertEqual(score_capability_status("verified"), 100.0)

    def test_status_scores_are_strictly_decreasing_in_law_3_10_order(self):
        ordered = ["verified", "measured", "assumed"]
        scores = [score_capability_status(status) for status in ordered]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(a > b for a, b in zip(scores, scores[1:])))

    def test_unsupported_and_unknown_score_identically_at_zero(self):
        self.assertEqual(score_capability_status("unsupported"), 0.0)
        self.assertEqual(score_capability_status("unknown"), 0.0)


class EvaluateShotFitTests(unittest.TestCase):
    def test_qualified_provider_scores_average_of_acceptance_named_capabilities(self):
        shot = _shot(acceptance={"identity": 95.0, "lip_sync": 90.0})
        profile = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=3,
            supported_camera_motions=("slow_push",),
            capabilities=(build_capability("identity", "verified"), build_capability("lip_sync", "measured")),
        )
        score = evaluate_shot_fit(shot, profile)
        self.assertFalse(score.disqualified)
        self.assertEqual(score.capability_scores, {"identity": 100.0, "lip_sync": 80.0})
        self.assertEqual(score.overall_score, 90.0)

    def test_undeclared_capability_scores_zero_but_does_not_disqualify(self):
        shot = _shot(lip_sync_required=False, acceptance={"identity": 95.0, "world": 90.0})
        profile = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=3,
            supported_camera_motions=("slow_push",), capabilities=(build_capability("identity", "verified"),),
        )
        score = evaluate_shot_fit(shot, profile)
        self.assertFalse(score.disqualified)
        self.assertEqual(score.capability_scores["world"], 0.0)

    def test_duration_exceeding_max_disqualifies(self):
        shot = _shot(lip_sync_required=False, start_seconds=0.0, end_seconds=20.0)
        profile = build_capability_profile(
            provider="veo", max_duration_seconds=6.0, max_character_count=3, supported_camera_motions=("slow_push",),
        )
        score = evaluate_shot_fit(shot, profile)
        self.assertTrue(score.disqualified)
        self.assertEqual(score.overall_score, 0.0)
        self.assertEqual(score.capability_scores, {})
        self.assertTrue(any("duration" in reason for reason in score.disqualification_reasons))

    def test_character_count_exceeding_max_disqualifies(self):
        shot = _shot(lip_sync_required=False, character_count=5)
        profile = build_capability_profile(
            provider="veo", max_duration_seconds=15.0, max_character_count=1, supported_camera_motions=("slow_push",),
        )
        score = evaluate_shot_fit(shot, profile)
        self.assertTrue(score.disqualified)
        self.assertTrue(any("character_count" in reason for reason in score.disqualification_reasons))

    def test_unsupported_camera_motion_disqualifies(self):
        shot = _shot(lip_sync_required=False, camera_motion="whip_pan")
        profile = build_capability_profile(
            provider="veo", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("slow_push",),
        )
        score = evaluate_shot_fit(shot, profile)
        self.assertTrue(score.disqualified)
        self.assertTrue(any("camera_motion" in reason for reason in score.disqualification_reasons))

    def test_required_lip_sync_with_no_capability_declared_disqualifies(self):
        shot = _shot(lip_sync_required=True)
        profile = build_capability_profile(
            provider="veo", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("slow_push",),
        )
        score = evaluate_shot_fit(shot, profile)
        self.assertTrue(score.disqualified)
        self.assertTrue(any("lip_sync" in reason for reason in score.disqualification_reasons))

    def test_required_lip_sync_with_unsupported_status_disqualifies(self):
        shot = _shot(lip_sync_required=True)
        profile = build_capability_profile(
            provider="veo", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("lip_sync", "unsupported"),),
        )
        score = evaluate_shot_fit(shot, profile)
        self.assertTrue(score.disqualified)

    def test_required_lip_sync_with_assumed_status_qualifies(self):
        shot = _shot(lip_sync_required=True, acceptance={"lip_sync": 90.0})
        profile = build_capability_profile(
            provider="veo", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("lip_sync", "assumed"),),
        )
        score = evaluate_shot_fit(shot, profile)
        self.assertFalse(score.disqualified)


class RankProvidersForShotTests(unittest.TestCase):
    def test_shot_requirements_produce_a_provider_fit_report(self):
        """Release 0.5's stated acceptance test (spec section 19): shot
        requirements produce a provider-fit report."""
        shot = _shot(acceptance={"identity": 95.0, "lip_sync": 90.0})
        kling = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=3,
            supported_camera_motions=("slow_push", "static"),
            capabilities=(build_capability("identity", "verified"), build_capability("lip_sync", "measured")),
        )
        veo = build_capability_profile(
            provider="veo", max_duration_seconds=6.0, max_character_count=1, supported_camera_motions=("slow_push",),
        )

        report = rank_providers_for_shot(shot, (veo, kling))

        self.assertEqual(report.shot_id, shot.id)
        self.assertEqual(report.recommended_provider, "kling")
        self.assertEqual([score.provider for score in report.scores], ["kling", "veo"])
        self.assertFalse(report.scores[0].disqualified)
        self.assertTrue(report.scores[1].disqualified)

    def test_all_disqualified_has_no_recommendation(self):
        shot = _shot(lip_sync_required=True)
        veo = build_capability_profile(
            provider="veo", max_duration_seconds=1.0, max_character_count=1, supported_camera_motions=("static",),
        )
        report = rank_providers_for_shot(shot, (veo,))
        self.assertIsNone(report.recommended_provider)
        self.assertTrue(report.scores[0].disqualified)

    def test_ranking_is_ordered_by_descending_score(self):
        shot = _shot(lip_sync_required=False, acceptance={"identity": 95.0})
        strong = build_capability_profile(
            provider="strong", max_duration_seconds=15.0, max_character_count=3,
            supported_camera_motions=("slow_push",), capabilities=(build_capability("identity", "verified"),),
        )
        weak = build_capability_profile(
            provider="weak", max_duration_seconds=15.0, max_character_count=3,
            supported_camera_motions=("slow_push",), capabilities=(build_capability("identity", "assumed"),),
        )
        report = rank_providers_for_shot(shot, (weak, strong))
        self.assertEqual([score.provider for score in report.scores], ["strong", "weak"])

    def test_tied_scores_break_ties_by_provider_name(self):
        shot = _shot(lip_sync_required=False, acceptance={"identity": 95.0})
        profile_b = build_capability_profile(
            provider="b_provider", max_duration_seconds=15.0, max_character_count=3,
            supported_camera_motions=("slow_push",), capabilities=(build_capability("identity", "verified"),),
        )
        profile_a = build_capability_profile(
            provider="a_provider", max_duration_seconds=15.0, max_character_count=3,
            supported_camera_motions=("slow_push",), capabilities=(build_capability("identity", "verified"),),
        )
        report = rank_providers_for_shot(shot, (profile_b, profile_a))
        self.assertEqual([score.provider for score in report.scores], ["a_provider", "b_provider"])


if __name__ == "__main__":
    unittest.main()
