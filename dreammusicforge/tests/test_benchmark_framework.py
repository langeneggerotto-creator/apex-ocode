from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from dreammusicforge.benchmark_framework import (
    build_evidence_record,
    score_benchmark,
    update_capability_profile,
    validate_benchmark,
    validate_profile,
    verify_provider_fit,
)

ROOT = Path(__file__).parents[1]
BENCHMARK = ROOT / "benchmarks" / "benchmark_006_sustained_phrase.json"
PROFILE = ROOT / "providers" / "kling" / "profile_v0.1.json"


class BenchmarkFrameworkTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(BENCHMARK.read_text(encoding="utf-8"))
        self.profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        self.passing_metrics = {
            "identity": 97,
            "hair": 99,
            "wardrobe": 99,
            "stage": 97,
            "camera": 94,
            "lighting": 93,
            "audio": 99,
            "lip_sync": 93,
            "pose": 94,
            "seam_invisibility": 92,
        }

    def test_profile_validates(self):
        self.assertTrue(validate_profile(self.profile).valid)

    def test_benchmark_validates(self):
        result = validate_benchmark(self.spec)
        self.assertTrue(result.valid, result.errors)

    def test_provider_fit_passes(self):
        result = verify_provider_fit(self.spec, self.profile)
        self.assertTrue(result.valid, result.errors)

    def test_provider_duration_limit_fails_closed(self):
        profile = copy.deepcopy(self.profile)
        profile["max_duration_seconds"] = 5
        result = verify_provider_fit(self.spec, profile)
        self.assertFalse(result.valid)
        self.assertTrue(any("exceeds provider limit" in error for error in result.errors))

    def test_missing_capability_fails_closed(self):
        profile = copy.deepcopy(self.profile)
        profile["capabilities"]["last_frame_seed"] = False
        result = verify_provider_fit(self.spec, profile)
        self.assertFalse(result.valid)
        self.assertTrue(any("last_frame_seed" in error for error in result.errors))

    def test_broken_state_inheritance_fails(self):
        spec = copy.deepcopy(self.spec)
        spec["segments"][1]["source_state_id"] = "STATE-WRONG"
        result = validate_benchmark(spec)
        self.assertFalse(result.valid)
        self.assertTrue(any("breaks reality-state inheritance" in error for error in result.errors))

    def test_weight_total_fails(self):
        spec = copy.deepcopy(self.spec)
        spec["dimensions"]["identity"]["weight"] = 0.5
        result = validate_benchmark(spec)
        self.assertFalse(result.valid)
        self.assertTrue(any("weights must total" in error for error in result.errors))

    def test_passing_result_is_accepted(self):
        result = score_benchmark(self.spec, self.profile, self.passing_metrics)
        self.assertTrue(result.passed)
        self.assertEqual([], result.failures)
        evidence = build_evidence_record(self.spec, self.profile, result)
        self.assertEqual("ACCEPT", evidence["promotion_decision"])
        self.assertEqual(64, len(result.evidence_hash))

    def test_single_critical_failure_rejects(self):
        metrics = dict(self.passing_metrics)
        metrics["hair"] = 50
        result = score_benchmark(self.spec, self.profile, metrics)
        self.assertFalse(result.passed)
        self.assertTrue(any("hair" in failure for failure in result.failures))

    def test_missing_metric_fails_closed(self):
        metrics = dict(self.passing_metrics)
        metrics.pop("audio")
        with self.assertRaisesRegex(ValueError, "Missing measured metric: audio"):
            score_benchmark(self.spec, self.profile, metrics)

    def test_capability_profile_updates_from_evidence(self):
        result = score_benchmark(self.spec, self.profile, self.passing_metrics)
        updated = update_capability_profile(self.profile, [result])
        self.assertEqual("MEASURED", updated["evidence_status"])
        self.assertEqual(97, updated["measured_averages"]["identity"])
        self.assertEqual(1, len(updated["benchmark_history"]))


if __name__ == "__main__":
    unittest.main()
