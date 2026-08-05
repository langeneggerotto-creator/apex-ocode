from __future__ import annotations

import unittest

from dreammusicforge.repair.classifier import DEFAULT_CRITICAL_THRESHOLDS, classify_failures


class ClassifyFailuresTests(unittest.TestCase):
    def test_no_metrics_below_threshold_produces_no_defects(self):
        defects = classify_failures({"audio": 100.0, "duration_frame_rate": 100.0}, "SHOT-x")
        self.assertEqual(defects, ())

    def test_metric_below_threshold_produces_a_defect(self):
        defects = classify_failures({"continuity": 67.4}, "SHOT-x")
        self.assertEqual(len(defects), 1)
        self.assertEqual(defects[0].type, "continuity")
        self.assertEqual(defects[0].shot_id, "SHOT-x")

    def test_this_repository_s_real_shot1_shot2_case(self):
        """These exact numbers come from running Release 0.9's real
        seam-comparison tooling against two real Kling AI 3.0 clips the
        user confirmed were supposed to be visually identical (same
        performer, same costume, same hair, same stage) but weren't --
        continuity 67.4 falls below the 70.0 default threshold, and this
        is the concrete real-world case that grounded this release's
        design, not a synthetic fixture."""
        metrics = {"duration_frame_rate": 100.0, "audio": 100.0, "continuity": 67.374, "color_continuity": 94.0667}
        defects = classify_failures(metrics, "SHOT-shot2-real")
        self.assertEqual(len(defects), 1)
        self.assertEqual(defects[0].type, "continuity")
        self.assertIn("regenerate", defects[0].recommendations)

    def test_multiple_failing_metrics_produce_multiple_defects(self):
        defects = classify_failures({"continuity": 40.0, "audio": 0.0}, "SHOT-x")
        self.assertEqual({defect.type for defect in defects}, {"continuity", "audio"})

    def test_defects_ordered_worst_first(self):
        defects = classify_failures({"continuity": 60.0, "audio": 10.0}, "SHOT-x")
        self.assertEqual([defect.type for defect in defects], ["audio", "continuity"])

    def test_custom_thresholds_override_defaults(self):
        defects = classify_failures({"continuity": 67.4}, "SHOT-x", thresholds={"continuity": 50.0})
        self.assertEqual(defects, ())

    def test_unlisted_metric_uses_default_threshold(self):
        defects = classify_failures({"custom_metric": 50.0}, "SHOT-x")
        self.assertEqual(len(defects), 1)
        self.assertEqual(defects[0].type, "custom_metric")

    def test_lip_sync_recommends_the_spec_example_action_first(self):
        """spec section 6.11's own worked example repairs a lip_sync
        failure with `dedicated_lip_sync_pass`, not one of section 8.9's
        six generic actions -- this release reuses that exact mapping."""
        defects = classify_failures({"lip_sync": 10.0}, "SHOT-x")
        self.assertEqual(defects[0].recommendations[0], "dedicated_lip_sync_pass")

    def test_severity_scales_with_how_far_below_threshold(self):
        just_below = classify_failures({"continuity": 69.0}, "SHOT-x", thresholds={"continuity": 70.0})
        far_below = classify_failures({"continuity": 10.0}, "SHOT-x", thresholds={"continuity": 70.0})
        self.assertNotEqual(just_below[0].severity, far_below[0].severity)
        self.assertEqual(far_below[0].severity, "critical")

    def test_default_thresholds_cover_every_metric_this_repository_can_measure(self):
        for metric_name in ("duration_frame_rate", "audio", "continuity", "color_continuity"):
            self.assertIn(metric_name, DEFAULT_CRITICAL_THRESHOLDS)


if __name__ == "__main__":
    unittest.main()
