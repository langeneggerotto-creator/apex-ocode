from __future__ import annotations

import unittest

from dreammusicforge.capability_atlas.builder import build_capability, build_capability_profile
from dreammusicforge.capability_atlas.scoring import rank_providers_for_shot
from dreammusicforge.production.models import Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming
from dreammusicforge.providers.kling.compiler import compile_kling_package, compile_kling_packages
from dreammusicforge.providers.kling.errors import KlingCompilerError
from dreammusicforge.providers.kling.models import KLING_NEGATIVE_PROMPT_BASELINE, KlingProfile
from dreammusicforge.slicer.builder import slice_shot
from dreammusicforge.slicer.models import RenderTask


def _shot(character_count=1, duration=6.5, lip_sync_required=True):
    return Shot(
        id="SHOT-deadbeef", sequence_id="SEQ-deadbeef",
        timing=ShotTiming(start_seconds=42.0, end_seconds=42.0 + duration, song_section="chorus_1"),
        purpose=ShotPurpose(semantic_event_id="SEM-deadbeef", narrative_function="declaration", editorial_function="chorus_hero_shot"),
        requirements=ShotRequirements(
            performer_id="PERFORMER-deadbeef", costume_id="COSTUME-deadbeef", world_id="WORLD-deadbeef",
            lip_sync_required=lip_sync_required, choreography_complexity="medium", camera_motion="slow_push",
            character_count=character_count,
        ),
        continuity=ShotContinuity(inherited_state="concealed", permitted_mutations=(), destination_state="revealed"),
        acceptance={"identity": 95.0, "lip_sync": 90.0},
    )


def _direct_task(shot):
    return RenderTask(
        id="RENDER-deadbeef", shot_id=shot.id, slice_id="SLICE-deadbeef", provider="kling",
        duration_seconds=shot.timing.end_seconds - shot.timing.start_seconds,
        required_assets=(shot.requirements.performer_id, shot.requirements.costume_id, shot.requirements.world_id),
        critical_checks=("identity", "lip_sync"),
    )


class CompileKlingPackageTests(unittest.TestCase):
    def test_fresh_task_compiles_to_image_to_video(self):
        shot = _shot()
        task = _direct_task(shot)
        profile = KlingProfile(max_duration_seconds=15.0)
        package = compile_kling_package(task, shot, profile)
        self.assertEqual(package.mode, "image_to_video")
        self.assertEqual(package.render_task_id, task.id)
        self.assertEqual(package.shot_id, shot.id)
        self.assertEqual(package.duration_seconds, task.duration_seconds)
        self.assertEqual(package.negative_prompt, KLING_NEGATIVE_PROMPT_BASELINE)
        self.assertIn("declaration", package.prompt)
        self.assertIn("chorus_1", package.prompt)

    def test_continuation_task_compiles_to_video_extension(self):
        shot = _shot()
        task = RenderTask(
            id="RENDER-cont", shot_id=shot.id, slice_id="SLICE-2", provider="kling", duration_seconds=5.0,
            required_assets=(shot.requirements.performer_id, "RENDER-deadbeef.mp4"),
        )
        profile = KlingProfile(max_duration_seconds=15.0)
        package = compile_kling_package(task, shot, profile)
        self.assertEqual(package.mode, "video_extension")

    def test_reference_manifest_overrides_expand_asset_ids(self):
        shot = _shot()
        task = _direct_task(shot)
        profile = KlingProfile(max_duration_seconds=15.0)
        package = compile_kling_package(
            task, shot, profile,
            reference_manifest_overrides={shot.requirements.performer_id: ("face_front.png", "full_body_front.png")},
        )
        self.assertIn("face_front.png", package.reference_manifest)
        self.assertIn("full_body_front.png", package.reference_manifest)
        self.assertIn(shot.requirements.costume_id, package.reference_manifest)

    def test_unsupported_mode_raises(self):
        shot = _shot()
        task = _direct_task(shot)
        profile = KlingProfile(max_duration_seconds=15.0, supported_modes=("video_extension",))
        with self.assertRaises(KlingCompilerError):
            compile_kling_package(task, shot, profile)

    def test_duration_exceeding_profile_limit_raises(self):
        shot = _shot(duration=20.0)
        task = _direct_task(shot)
        profile = KlingProfile(max_duration_seconds=15.0)
        with self.assertRaises(KlingCompilerError):
            compile_kling_package(task, shot, profile)

    def test_mismatched_shot_raises(self):
        shot = _shot()
        task = RenderTask(id="RENDER-x", shot_id="SHOT-someone-else", slice_id="SLICE-x", provider="kling", duration_seconds=5.0, required_assets=("PERFORMER-deadbeef",))
        profile = KlingProfile(max_duration_seconds=15.0)
        with self.assertRaises(KlingCompilerError):
            compile_kling_package(task, shot, profile)


class CompileKlingPackagesTests(unittest.TestCase):
    def test_each_task_produces_an_operator_usable_kling_package(self):
        """Release 0.7's stated acceptance test (spec section 19): each
        task produces an operator-usable Kling package."""
        shot = _shot(character_count=5, duration=6.5)  # forces layered_compositing -> multiple tasks
        kling = build_capability_profile(
            provider="kling", max_duration_seconds=15.0, max_character_count=8, supported_camera_motions=("slow_push",),
            capabilities=(build_capability("identity", "verified"), build_capability("lip_sync", "measured")),
        )
        report = rank_providers_for_shot(shot, (kling,))
        slice_result = slice_shot(shot, report, {"kling": kling})
        self.assertGreater(len(slice_result.render_tasks), 1)

        profile = KlingProfile(max_duration_seconds=15.0)
        packages = compile_kling_packages(slice_result.render_tasks, shot, profile)

        self.assertEqual(len(packages), len(slice_result.render_tasks))
        for package in packages:
            self.assertTrue(package.prompt.strip())
            self.assertTrue(package.negative_prompt)
            self.assertTrue(package.reference_manifest)
            self.assertLessEqual(package.duration_seconds, package.duration_limit_seconds)
            self.assertIn(package.mode, ("image_to_video", "video_extension"))

    def test_empty_render_tasks_produces_empty_packages(self):
        shot = _shot()
        profile = KlingProfile(max_duration_seconds=15.0)
        self.assertEqual(compile_kling_packages((), shot, profile), ())


if __name__ == "__main__":
    unittest.main()
