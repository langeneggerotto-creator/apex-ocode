from __future__ import annotations

import unittest

from dreammusicforge.capability_atlas.builder import build_capability, build_capability_profile
from dreammusicforge.capability_atlas.scoring import rank_providers_for_shot
from dreammusicforge.production.models import Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming
from dreammusicforge.slicer.builder import slice_shot
from dreammusicforge.slicer.models import EXPECTED_RENDER_OUTPUTS


def _shot(character_count=1, choreography_complexity="low", camera_motion="slow_push", lip_sync_required=False, duration=6.0, acceptance=None):
    return Shot(
        id="SHOT-deadbeef", sequence_id="SEQ-deadbeef",
        timing=ShotTiming(start_seconds=10.0, end_seconds=10.0 + duration, song_section="verse_1"),
        purpose=ShotPurpose(semantic_event_id="SEM-deadbeef", narrative_function="n", editorial_function="e"),
        requirements=ShotRequirements(
            performer_id="PERFORMER-deadbeef", costume_id="COSTUME-deadbeef", world_id="WORLD-deadbeef",
            lip_sync_required=lip_sync_required, choreography_complexity=choreography_complexity,
            camera_motion=camera_motion, character_count=character_count,
        ),
        continuity=ShotContinuity(inherited_state="a", permitted_mutations=(), destination_state="b"),
        acceptance=acceptance if acceptance is not None else {"identity": 95.0},
    )


class SliceShotDirectRenderTests(unittest.TestCase):
    def test_produces_one_render_task_spanning_the_whole_shot(self):
        shot = _shot(duration=6.0)
        kling = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("identity", "verified"),),
        )
        report = rank_providers_for_shot(shot, (kling,))
        result = slice_shot(shot, report, {"kling": kling})

        self.assertEqual(result.strategy, "direct_render")
        self.assertEqual(len(result.render_tasks), 1)
        self.assertEqual(result.render_tasks[0].duration_seconds, 6.0)
        self.assertEqual(result.render_tasks[0].provider, "kling")
        self.assertEqual(result.render_tasks[0].expected_outputs, EXPECTED_RENDER_OUTPUTS)
        self.assertEqual(len(result.temporal_slices), 1)
        self.assertEqual(result.visual_layers, ())
        self.assertIsNone(result.fallback_plan)


class SliceShotLayeredCompositingTests(unittest.TestCase):
    def test_complex_shot_becomes_executable_render_tasks(self):
        """Release 0.6's stated acceptance test (spec section 19):
        complex shot becomes executable render tasks."""
        shot = _shot(character_count=5, choreography_complexity="high", lip_sync_required=True, duration=20.0, acceptance={"identity": 95.0, "lip_sync": 90.0})
        kling = build_capability_profile(
            provider="kling", max_duration_seconds=25.0, max_character_count=8, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("identity", "verified"), build_capability("lip_sync", "measured")),
        )
        report = rank_providers_for_shot(shot, (kling,))

        result = slice_shot(shot, report, {"kling": kling})

        self.assertEqual(result.strategy, "layered_compositing")
        self.assertGreater(len(result.render_tasks), 1)
        self.assertTrue(all(task.provider == "kling" for task in result.render_tasks))
        self.assertTrue(all(task.duration_seconds == 20.0 for task in result.render_tasks))
        layer_names = {layer.name for layer in result.visual_layers}
        self.assertEqual(layer_names, {"world_pass", "performer_pass", "lip_sync_pass"})
        self.assertEqual(len(result.motion_layers), 1)
        self.assertIsNone(result.fallback_plan)

    def test_visual_layer_ids_match_render_task_slice_ids(self):
        shot = _shot(character_count=5, duration=6.0)
        kling = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=8, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("identity", "verified"),),
        )
        report = rank_providers_for_shot(shot, (kling,))
        result = slice_shot(shot, report, {"kling": kling})
        self.assertEqual({layer.id for layer in result.visual_layers}, {task.slice_id for task in result.render_tasks})


class SliceShotControlledContinuationTests(unittest.TestCase):
    def test_splits_long_shot_into_provider_fitting_chunks(self):
        shot = _shot(duration=20.0)
        veo = build_capability_profile(
            provider="veo", max_duration_seconds=6.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("video_extension", "verified"),),
        )
        report = rank_providers_for_shot(shot, (veo,))
        result = slice_shot(shot, report, {"veo": veo})

        self.assertEqual(result.strategy, "controlled_continuation")
        self.assertEqual(len(result.temporal_slices), 4)  # ceil(20/6) == 4
        self.assertTrue(all(task.duration_seconds <= 6.0 for task in result.render_tasks))
        total_duration = sum(task.duration_seconds for task in result.render_tasks)
        self.assertAlmostEqual(total_duration, 20.0, places=6)

    def test_slices_cover_the_shot_contiguously_without_gaps(self):
        shot = _shot(duration=20.0)
        veo = build_capability_profile(
            provider="veo", max_duration_seconds=6.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("video_extension", "verified"),),
        )
        report = rank_providers_for_shot(shot, (veo,))
        result = slice_shot(shot, report, {"veo": veo})
        ordered = sorted(result.temporal_slices, key=lambda item: item.index)
        self.assertEqual(ordered[0].start_seconds, shot.timing.start_seconds)
        self.assertEqual(ordered[-1].end_seconds, shot.timing.end_seconds)
        for previous, current in zip(ordered, ordered[1:]):
            self.assertEqual(previous.end_seconds, current.start_seconds)

    def test_continuation_tasks_after_the_first_reference_the_previous_task(self):
        shot = _shot(duration=20.0)
        veo = build_capability_profile(
            provider="veo", max_duration_seconds=6.0, max_character_count=3, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("video_extension", "verified"),),
        )
        report = rank_providers_for_shot(shot, (veo,))
        result = slice_shot(shot, report, {"veo": veo})
        first, *rest = result.render_tasks
        self.assertFalse(any(asset.endswith(".mp4") for asset in first.required_assets))
        for task in rest:
            self.assertTrue(any(asset.endswith(".mp4") for asset in task.required_assets))


class SliceShotExternalProductionRequiredTests(unittest.TestCase):
    def test_produces_no_render_tasks_but_a_fallback_plan(self):
        shot = _shot(camera_motion="whip_pan")
        veo = build_capability_profile(provider="veo", max_duration_seconds=15.0, max_character_count=3, supported_camera_motions=("static",))
        report = rank_providers_for_shot(shot, (veo,))
        result = slice_shot(shot, report, {"veo": veo})

        self.assertEqual(result.strategy, "external_production_required")
        self.assertEqual(result.render_tasks, ())
        self.assertIsNotNone(result.fallback_plan)
        self.assertIn("specialist tool", result.fallback_plan.recommended_action)


if __name__ == "__main__":
    unittest.main()
