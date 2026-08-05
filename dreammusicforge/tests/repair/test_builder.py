from __future__ import annotations

import unittest

from dreammusicforge.repair.builder import build_repair_plan, evaluate_candidate
from dreammusicforge.repair.classifier import classify_failures
from dreammusicforge.repair.errors import AcceptanceRepairError


class BuildRepairPlanTests(unittest.TestCase):
    def test_single_defect_uses_its_top_recommendation(self):
        metrics = {"color_continuity": 30.0, "audio": 100.0}
        defects = classify_failures(metrics, "SHOT-x")
        plan = build_repair_plan(defects, metrics, "SHOT-x")
        self.assertEqual(plan.action, "use_light_flash")

    def test_multiple_defects_collapse_to_regenerate(self):
        metrics = {"continuity": 40.0, "color_continuity": 30.0, "audio": 100.0}
        defects = classify_failures(metrics, "SHOT-x")
        plan = build_repair_plan(defects, metrics, "SHOT-x")
        self.assertEqual(plan.action, "regenerate")

    def test_a_regenerate_recommendation_forces_the_whole_plan_to_regenerate(self):
        metrics = {"audio": 10.0}  # audio's only recommendation is "regenerate"
        defects = classify_failures(metrics, "SHOT-x")
        plan = build_repair_plan(defects, metrics, "SHOT-x")
        self.assertEqual(plan.action, "regenerate")

    def test_preserve_names_every_metric_that_did_not_fail(self):
        metrics = {"continuity": 40.0, "audio": 100.0, "duration_frame_rate": 100.0}
        defects = classify_failures(metrics, "SHOT-x")
        plan = build_repair_plan(defects, metrics, "SHOT-x")
        self.assertEqual(set(plan.preserve), {"audio", "duration_frame_rate"})
        self.assertNotIn("continuity", plan.preserve)

    def test_plan_is_bounded_to_one_shot_and_one_action(self):
        metrics = {"continuity": 20.0, "audio": 10.0, "color_continuity": 5.0}
        defects = classify_failures(metrics, "SHOT-x")
        plan = build_repair_plan(defects, metrics, "SHOT-x")
        self.assertEqual(plan.shot_id, "SHOT-x")
        self.assertIsInstance(plan.action, str)
        self.assertTrue(plan.action)


class EvaluateCandidateTests(unittest.TestCase):
    def test_clean_candidate_is_accepted(self):
        result = evaluate_candidate(
            candidate_id="CANDIDATE-x", shot_id="SHOT-x",
            metrics={"audio": 100.0, "duration_frame_rate": 100.0},
        )
        self.assertEqual(result.decision, "accept")
        self.assertEqual(result.defects, ())
        self.assertIsNone(result.repair)
        self.assertEqual(result.overall_score, 100.0)

    def test_failed_candidate_produces_a_bounded_repair_plan(self):
        """Release 0.10's stated acceptance test (spec section 19):
        failed candidate produces a bounded repair plan. Numbers are
        the real measurements from running Release 0.9 against two
        actual Kling AI 3.0 clips the user confirmed should have been
        visually identical but weren't."""
        metrics = {"duration_frame_rate": 100.0, "audio": 100.0, "continuity": 67.374, "color_continuity": 94.0667}
        result = evaluate_candidate(candidate_id="CANDIDATE-shot2-real", shot_id="SHOT-shot2-real", metrics=metrics)

        self.assertEqual(result.decision, "reject")
        self.assertEqual(result.critical_failures, ("continuity",))
        self.assertIsNotNone(result.repair)
        self.assertEqual(result.repair.shot_id, "SHOT-shot2-real")
        self.assertEqual(result.repair.action, "regenerate")
        self.assertEqual(set(result.repair.preserve), {"duration_frame_rate", "audio", "color_continuity"})

    def test_custom_thresholds_change_the_decision(self):
        metrics = {"continuity": 67.374}
        strict = evaluate_candidate(candidate_id="CANDIDATE-x", shot_id="SHOT-x", metrics=metrics)
        lenient = evaluate_candidate(candidate_id="CANDIDATE-x", shot_id="SHOT-x", metrics=metrics, thresholds={"continuity": 50.0})
        self.assertEqual(strict.decision, "reject")
        self.assertEqual(lenient.decision, "accept")

    def test_overall_score_is_the_mean_of_all_metrics(self):
        result = evaluate_candidate(candidate_id="CANDIDATE-x", shot_id="SHOT-x", metrics={"a": 80.0, "b": 100.0})
        self.assertEqual(result.overall_score, 90.0)

    def test_result_validates_against_its_own_schema(self):
        result = evaluate_candidate(
            candidate_id="CANDIDATE-x", shot_id="SHOT-x", metrics={"continuity": 10.0},
        )
        from dreammusicforge.repair.schema import validate_verification_result_schema
        self.assertEqual(validate_verification_result_schema(result.to_dict()), [])


if __name__ == "__main__":
    unittest.main()
