from __future__ import annotations

import copy
import unittest

from dreammusicforge.repair.schema import (
    validate_defect_schema, validate_repair_plan_schema, validate_verification_result_schema,
)

VALID_DEFECT = {
    "id": "DEFECT-deadbeef", "type": "continuity", "severity": "high",
    "location": {"shot_id": "SHOT-deadbeef", "start": 9.9, "end": 10.0},
    "recommendations": ["regenerate"],
}
VALID_REPAIR_PLAN = {"shot_id": "SHOT-deadbeef", "action": "regenerate", "preserve": ["audio"]}
VALID_RESULT = {
    "candidate_id": "CANDIDATE-deadbeef", "metrics": {"continuity": 67.4, "audio": 100.0},
    "critical_failures": ["continuity"], "overall_score": 83.7, "decision": "reject",
    "defects": [VALID_DEFECT], "repair": VALID_REPAIR_PLAN,
}
ACCEPTED_RESULT = {
    "candidate_id": "CANDIDATE-deadbeef", "metrics": {"audio": 100.0},
    "critical_failures": [], "overall_score": 100.0, "decision": "accept",
}


class DefectSchemaTests(unittest.TestCase):
    def test_valid_defect_has_no_errors(self):
        self.assertEqual(validate_defect_schema(VALID_DEFECT), [])

    def test_malformed_id_is_rejected(self):
        data = dict(VALID_DEFECT, id="not-a-defect-id")
        errors = validate_defect_schema(data)
        self.assertTrue(any("id" in e for e in errors))

    def test_invalid_severity_is_rejected(self):
        data = dict(VALID_DEFECT, severity="catastrophic")
        errors = validate_defect_schema(data)
        self.assertTrue(any("severity" in e for e in errors))

    def test_start_after_end_is_rejected(self):
        data = dict(VALID_DEFECT, location={"shot_id": "SHOT-deadbeef", "start": 10.0, "end": 5.0})
        errors = validate_defect_schema(data)
        self.assertTrue(any("start" in e for e in errors))

    def test_null_start_and_end_are_accepted(self):
        data = dict(VALID_DEFECT, location={"shot_id": "SHOT-deadbeef", "start": None, "end": None})
        self.assertEqual(validate_defect_schema(data), [])

    def test_empty_recommendations_is_rejected(self):
        data = dict(VALID_DEFECT, recommendations=[])
        errors = validate_defect_schema(data)
        self.assertTrue(any("recommendations" in e for e in errors))


class RepairPlanSchemaTests(unittest.TestCase):
    def test_valid_plan_has_no_errors(self):
        self.assertEqual(validate_repair_plan_schema(VALID_REPAIR_PLAN), [])

    def test_missing_action_is_reported(self):
        data = {k: v for k, v in VALID_REPAIR_PLAN.items() if k != "action"}
        errors = validate_repair_plan_schema(data)
        self.assertTrue(any("action" in e for e in errors))

    def test_preserve_may_be_omitted(self):
        data = {k: v for k, v in VALID_REPAIR_PLAN.items() if k != "preserve"}
        self.assertEqual(validate_repair_plan_schema(data), [])


class VerificationResultSchemaTests(unittest.TestCase):
    def test_valid_rejected_result_has_no_errors(self):
        self.assertEqual(validate_verification_result_schema(VALID_RESULT), [])

    def test_valid_accepted_result_has_no_errors(self):
        self.assertEqual(validate_verification_result_schema(ACCEPTED_RESULT), [])

    def test_reject_without_repair_is_rejected(self):
        data = dict(VALID_RESULT, repair=None)
        errors = validate_verification_result_schema(data)
        self.assertTrue(any("repair is missing" in e for e in errors))

    def test_accept_with_repair_is_rejected(self):
        data = dict(ACCEPTED_RESULT, repair=VALID_REPAIR_PLAN)
        errors = validate_verification_result_schema(data)
        self.assertTrue(any("repair is present" in e for e in errors))

    def test_reject_without_critical_failures_is_rejected(self):
        data = dict(VALID_RESULT, critical_failures=[])
        errors = validate_verification_result_schema(data)
        self.assertTrue(any("critical_failures is empty" in e for e in errors))

    def test_accept_with_critical_failures_is_rejected(self):
        data = dict(ACCEPTED_RESULT, critical_failures=["continuity"])
        errors = validate_verification_result_schema(data)
        self.assertTrue(any("critical_failures is non-empty" in e for e in errors))

    def test_critical_failure_not_in_metrics_is_rejected(self):
        data = dict(VALID_RESULT, critical_failures=["nonexistent_metric"])
        errors = validate_verification_result_schema(data)
        self.assertTrue(any("not in metrics" in e for e in errors))

    def test_empty_metrics_is_rejected(self):
        data = dict(ACCEPTED_RESULT, metrics={})
        errors = validate_verification_result_schema(data)
        self.assertTrue(any("metrics" in e for e in errors))

    def test_invalid_nested_defect_is_reported(self):
        data = copy.deepcopy(VALID_RESULT)
        data["defects"][0]["severity"] = "catastrophic"
        errors = validate_verification_result_schema(data)
        self.assertTrue(any(e.startswith("defects[0]") for e in errors))

    def test_invalid_nested_repair_is_reported(self):
        data = copy.deepcopy(VALID_RESULT)
        del data["repair"]["action"]
        errors = validate_verification_result_schema(data)
        self.assertTrue(any(e.startswith("repair:") for e in errors))


if __name__ == "__main__":
    unittest.main()
