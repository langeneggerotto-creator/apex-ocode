from __future__ import annotations

import unittest

from dreammusicforge.capability_atlas.builder import build_capability, build_capability_profile
from dreammusicforge.capability_atlas.scoring import rank_providers_for_shot
from dreammusicforge.production.models import Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming
from dreammusicforge.slicer.models import SLICING_STRATEGIES
from dreammusicforge.slicer.strategy import select_strategy


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


class SelectStrategyTests(unittest.TestCase):
    def test_simple_qualified_shot_selects_direct_render(self):
        shot = _shot(character_count=1, choreography_complexity="low", duration=6.0)
        kling = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("identity", "verified"),),
        )
        report = rank_providers_for_shot(shot, (kling,))
        decision = select_strategy(shot, report, {"kling": kling})
        self.assertEqual(decision.strategy, "direct_render")
        self.assertEqual(decision.provider, "kling")
        self.assertIsNotNone(decision.risk_factors)

    def test_many_characters_selects_layered_compositing(self):
        shot = _shot(character_count=5, duration=6.0)
        kling = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=8, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("identity", "verified"),),
        )
        report = rank_providers_for_shot(shot, (kling,))
        decision = select_strategy(shot, report, {"kling": kling})
        self.assertEqual(decision.strategy, "layered_compositing")

    def test_weak_fit_score_selects_layered_compositing(self):
        shot = _shot(character_count=1, choreography_complexity="low", acceptance={"identity": 95.0})
        kling = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("identity", "assumed"),),  # 55.0 < 70.0 threshold
        )
        report = rank_providers_for_shot(shot, (kling,))
        decision = select_strategy(shot, report, {"kling": kling})
        self.assertEqual(decision.strategy, "layered_compositing")

    def test_duration_only_disqualification_with_continuation_support_selects_controlled_continuation(self):
        shot = _shot(duration=20.0)
        veo = build_capability_profile(
            provider="veo", max_duration_seconds=6.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("video_extension", "verified"),),
        )
        report = rank_providers_for_shot(shot, (veo,))
        decision = select_strategy(shot, report, {"veo": veo})
        self.assertEqual(decision.strategy, "controlled_continuation")
        self.assertEqual(decision.provider, "veo")

    def test_duration_only_disqualification_without_continuation_support_selects_external_production(self):
        shot = _shot(duration=20.0)
        veo = build_capability_profile(provider="veo", max_duration_seconds=6.0, max_character_count=3, supported_camera_motions=("slow_push",))
        report = rank_providers_for_shot(shot, (veo,))
        decision = select_strategy(shot, report, {"veo": veo})
        self.assertEqual(decision.strategy, "external_production_required")
        self.assertIsNone(decision.provider)
        self.assertIsNone(decision.risk_factors)

    def test_non_duration_disqualification_selects_external_production(self):
        shot = _shot(camera_motion="whip_pan")
        veo = build_capability_profile(provider="veo", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("static",))
        report = rank_providers_for_shot(shot, (veo,))
        decision = select_strategy(shot, report, {"veo": veo})
        self.assertEqual(decision.strategy, "external_production_required")

    def test_editorial_illusion_is_never_selected(self):
        """Documented boundary: this release never auto-selects
        editorial_illusion -- see strategy.py's module docstring."""
        cases = [
            (_shot(character_count=1, duration=6.0), ("kling", build_capability_profile(
                provider="kling", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("slow_push",),
                capabilities=(build_capability("identity", "verified"),),
            ))),
            (_shot(duration=20.0), ("veo", build_capability_profile(
                provider="veo", max_duration_seconds=6.0, max_character_count=3, supported_camera_motions=("slow_push",),
            ))),
        ]
        for shot, (provider_name, profile) in cases:
            report = rank_providers_for_shot(shot, (profile,))
            decision = select_strategy(shot, report, {provider_name: profile})
            self.assertNotEqual(decision.strategy, "editorial_illusion")

    def test_every_returned_strategy_is_a_known_strategy(self):
        shot = _shot()
        kling = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("identity", "verified"),),
        )
        report = rank_providers_for_shot(shot, (kling,))
        decision = select_strategy(shot, report, {"kling": kling})
        self.assertIn(decision.strategy, SLICING_STRATEGIES)


if __name__ == "__main__":
    unittest.main()
