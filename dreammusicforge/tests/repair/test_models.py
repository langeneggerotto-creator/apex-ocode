from __future__ import annotations

import unittest

from dreammusicforge.repair.models import Defect, RepairPlan, VerificationResult

DEFECT_DATA = {
    "id": "DEFECT-deadbeef", "type": "continuity", "severity": "high",
    "location": {"shot_id": "SHOT-deadbeef", "start": None, "end": None},
    "recommendations": ["regenerate", "cut_away_before_defect"],
}
REPAIR_PLAN_DATA = {"shot_id": "SHOT-deadbeef", "action": "regenerate", "preserve": ["audio", "duration_frame_rate"]}

VERIFICATION_RESULT_DATA = {
    "candidate_id": "CANDIDATE-deadbeef", "metrics": {"continuity": 67.4, "audio": 100.0},
    "critical_failures": ["continuity"], "overall_score": 83.7, "decision": "reject",
    "defects": [DEFECT_DATA], "repair": REPAIR_PLAN_DATA,
}


class DefectRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        defect = Defect.from_dict(DEFECT_DATA)
        self.assertEqual(defect.to_dict(), DEFECT_DATA)

    def test_missing_location_bounds_default_to_none(self):
        data = {**DEFECT_DATA, "location": {"shot_id": "SHOT-deadbeef"}}
        defect = Defect.from_dict(data)
        self.assertIsNone(defect.start_seconds)
        self.assertIsNone(defect.end_seconds)

    def test_defect_is_frozen(self):
        defect = Defect.from_dict(DEFECT_DATA)
        with self.assertRaises(Exception):
            defect.severity = "low"  # type: ignore[misc]


class RepairPlanRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        plan = RepairPlan.from_dict(REPAIR_PLAN_DATA)
        self.assertEqual(plan.to_dict(), REPAIR_PLAN_DATA)

    def test_missing_preserve_defaults_to_empty_tuple(self):
        data = {k: v for k, v in REPAIR_PLAN_DATA.items() if k != "preserve"}
        plan = RepairPlan.from_dict(data)
        self.assertEqual(plan.preserve, ())


class VerificationResultRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        result = VerificationResult.from_dict(VERIFICATION_RESULT_DATA)
        self.assertEqual(result.to_dict(), VERIFICATION_RESULT_DATA)

    def test_accepted_result_has_no_repair_or_defects(self):
        data = {
            "candidate_id": "CANDIDATE-deadbeef", "metrics": {"audio": 100.0},
            "critical_failures": [], "overall_score": 100.0, "decision": "accept",
        }
        result = VerificationResult.from_dict(data)
        self.assertEqual(result.defects, ())
        self.assertIsNone(result.repair)

    def test_result_is_frozen(self):
        result = VerificationResult.from_dict(VERIFICATION_RESULT_DATA)
        with self.assertRaises(Exception):
            result.decision = "accept"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
