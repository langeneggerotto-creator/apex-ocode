from __future__ import annotations

import unittest

from dreammusicforge.production.models import Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming
from dreammusicforge.providers.runway.compiler import compile_runway_package, compile_runway_packages
from dreammusicforge.providers.runway.errors import RunwayCompilerError
from dreammusicforge.providers.runway.models import RunwayProfile
from dreammusicforge.slicer.models import RenderTask


def _shot(duration=6.5):
    return Shot(
        id="SHOT-deadbeef", sequence_id="SEQ-deadbeef",
        timing=ShotTiming(start_seconds=42.0, end_seconds=42.0 + duration, song_section="chorus_1"),
        purpose=ShotPurpose(semantic_event_id="SEM-deadbeef", narrative_function="declaration", editorial_function="chorus_hero_shot"),
        requirements=ShotRequirements(
            performer_id="PERFORMER-deadbeef", costume_id="COSTUME-deadbeef", world_id="WORLD-deadbeef",
            lip_sync_required=True, choreography_complexity="medium", camera_motion="slow_push", character_count=1,
        ),
        continuity=ShotContinuity(inherited_state="concealed", permitted_mutations=(), destination_state="revealed"),
        acceptance={"identity": 95.0},
    )


def _task(shot):
    return RenderTask(
        id="RENDER-deadbeef", shot_id=shot.id, slice_id="SLICE-deadbeef", provider="runway",
        duration_seconds=shot.timing.end_seconds - shot.timing.start_seconds,
        required_assets=(shot.requirements.performer_id, shot.requirements.costume_id, shot.requirements.world_id),
    )


class CompileRunwayPackageTests(unittest.TestCase):
    def test_image_to_video_with_prompt_image_compiles(self):
        shot = _shot(duration=6.5)
        task = _task(shot)
        profile = RunwayProfile(model="gen4_turbo")
        package = compile_runway_package(task, shot, profile, prompt_image="https://example.com/ref.png")

        self.assertTrue(package.id.startswith("RUNWAY-"))
        self.assertEqual(package.mode, "image_to_video")
        self.assertEqual(package.prompt_image, "https://example.com/ref.png")
        self.assertEqual(package.render_task_id, task.id)
        self.assertEqual(package.reference_manifest, task.required_assets)
        self.assertIn("chorus_1", package.prompt_text)

    def test_image_to_video_without_prompt_image_raises(self):
        shot = _shot()
        task = _task(shot)
        profile = RunwayProfile(model="gen4_turbo")
        with self.assertRaises(RunwayCompilerError):
            compile_runway_package(task, shot, profile)  # default mode is image_to_video, no prompt_image given

    def test_text_to_video_mode_needs_no_prompt_image(self):
        shot = _shot()
        task = _task(shot)
        profile = RunwayProfile(model="gen4_turbo")
        package = compile_runway_package(task, shot, profile, mode="text_to_video")
        self.assertEqual(package.mode, "text_to_video")
        self.assertIsNone(package.prompt_image)

    def test_duration_rounds_up_to_the_nearest_supported_option(self):
        shot = _shot(duration=6.5)  # between 5.0 and 10.0
        task = _task(shot)
        profile = RunwayProfile(model="gen4_turbo")
        package = compile_runway_package(task, shot, profile, prompt_image="ref.png")
        self.assertEqual(package.duration_seconds, 10.0)

    def test_duration_exceeding_the_largest_supported_option_raises(self):
        shot = _shot(duration=25.0)
        task = _task(shot)
        profile = RunwayProfile(model="gen4_turbo")
        with self.assertRaises(RunwayCompilerError):
            compile_runway_package(task, shot, profile, prompt_image="ref.png")

    def test_mode_not_in_profile_raises(self):
        shot = _shot()
        task = _task(shot)
        profile = RunwayProfile(model="gen4_turbo", supported_modes=("text_to_video",))
        with self.assertRaises(RunwayCompilerError):
            compile_runway_package(task, shot, profile, prompt_image="ref.png")  # defaults to image_to_video

    def test_mismatched_shot_raises(self):
        shot = _shot()
        task = _task(shot)
        other_shot = _shot()
        object.__setattr__(other_shot, "id", "SHOT-other")
        with self.assertRaises(RunwayCompilerError):
            compile_runway_package(task, other_shot, RunwayProfile(model="gen4_turbo"), prompt_image="ref.png")

    def test_compile_runway_packages_compiles_every_task(self):
        shot = _shot()
        task1 = _task(shot)
        task2 = RenderTask(id="RENDER-2", shot_id=shot.id, slice_id="SLICE-2", provider="runway", duration_seconds=4.0, required_assets=task1.required_assets)
        profile = RunwayProfile(model="gen4_turbo")
        packages = compile_runway_packages((task1, task2), shot, profile, prompt_image="ref.png")
        self.assertEqual(len(packages), 2)
        self.assertEqual({p.render_task_id for p in packages}, {task1.id, task2.id})


if __name__ == "__main__":
    unittest.main()
