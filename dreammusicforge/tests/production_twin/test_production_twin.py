import unittest

from dreammusicforge.production_twin import (
    CameraState,
    ExperienceState,
    LightingState,
    MusicState,
    PerformerState,
    ProductionTwin,
    TwinState,
    TwinTransition,
    WorldState,
    compile_renderer_tasks,
    validate_twin,
)


def state(state_id, start, end, *, costume="C1", hair="H1", world="W1", camera_move="slow_push", allowed=()):
    return TwinState(
        state_id=state_id,
        start_seconds=start,
        end_seconds=end,
        performer=PerformerState("P1", "IDENTITY-1", costume, hair, pose="singing", gaze="camera", action="sing"),
        camera=CameraState("medium", 50.0, "eye_level", camera_move, "A"),
        lighting=LightingState("L1", "soft_key", "blue_fill", "cyan_rim", "haze_medium", "BLUE-1"),
        music=MusicState("SONG-1", start, "VERSE", energy=0.5),
        experience=ExperienceState(f"E-{state_id}", "connection", 0.5, "viewer feels closer to performer"),
        world=WorldState(world, "GEO-1"),
        invariants=("identity", "master_song", "hair", "costume", "world"),
        allowed_mutations=allowed,
    )


class ProductionTwinTests(unittest.TestCase):
    def test_valid_twin_passes(self):
        s1 = state("S1", 0.0, 5.0)
        s2 = state("S2", 5.0, 10.0)
        twin = ProductionTwin("T1", "PRJ1", (s1, s2), (TwinTransition("TR1", "S1", "S2", (), "continue performance"),), 10.0)
        self.assertEqual(validate_twin(twin), ())

    def test_gap_fails(self):
        s1 = state("S1", 0.0, 4.0)
        s2 = state("S2", 5.0, 10.0)
        twin = ProductionTwin("T1", "PRJ1", (s1, s2), (TwinTransition("TR1", "S1", "S2", (), "gap"),), 10.0)
        self.assertTrue(any(i.code == "TIMELINE_GAP" for i in validate_twin(twin)))

    def test_identity_change_fails(self):
        s1 = state("S1", 0.0, 5.0)
        s2 = state("S2", 5.0, 10.0)
        object.__setattr__(s2.performer, "identity_id", "IDENTITY-2")
        twin = ProductionTwin("T1", "PRJ1", (s1, s2), (TwinTransition("TR1", "S1", "S2", ("identity",), "bad"),), 10.0)
        self.assertTrue(any(i.code == "INVARIANT_VIOLATION" for i in validate_twin(twin)))

    def test_undeclared_camera_mutation_fails(self):
        s1 = state("S1", 0.0, 5.0)
        s2 = state("S2", 5.0, 10.0, camera_move="orbit")
        twin = ProductionTwin("T1", "PRJ1", (s1, s2), (TwinTransition("TR1", "S1", "S2", ("camera",), "camera evolution"),), 10.0)
        self.assertTrue(any(i.code == "UNDECLARED_MUTATION" for i in validate_twin(twin)))

    def test_declared_camera_mutation_passes(self):
        s1 = state("S1", 0.0, 5.0, allowed=("camera",))
        s2 = state("S2", 5.0, 10.0, camera_move="orbit", allowed=("camera",))
        twin = ProductionTwin("T1", "PRJ1", (s1, s2), (TwinTransition("TR1", "S1", "S2", ("camera",), "camera evolution"),), 10.0)
        self.assertEqual(validate_twin(twin), ())

    def test_missing_transition_fails(self):
        s1 = state("S1", 0.0, 5.0)
        s2 = state("S2", 5.0, 10.0)
        twin = ProductionTwin("T1", "PRJ1", (s1, s2), (), 10.0)
        self.assertTrue(any(i.code == "MISSING_TRANSITION" for i in validate_twin(twin)))

    def test_renderer_contract_is_provider_neutral(self):
        s1 = state("S1", 0.0, 5.0, allowed=("camera",))
        s2 = state("S2", 5.0, 10.0, camera_move="orbit", allowed=("camera",))
        twin = ProductionTwin("T1", "PRJ1", (s1, s2), (TwinTransition("TR1", "S1", "S2", ("camera",), "camera evolution"),), 10.0)
        tasks = compile_renderer_tasks(twin)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].performer_id, "P1")
        self.assertIn("camera", tasks[0].permitted_changes)
        self.assertFalse(hasattr(tasks[0], "provider"))


if __name__ == "__main__":
    unittest.main()
