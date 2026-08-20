from __future__ import annotations

import unittest

from dreammusicforge.operator_studio.schema import validate_operator_report_schema

from .sample_data import ACCEPTED_RESULT, SAMPLE_EXPORT_MANIFEST, SAMPLE_FINISHING_RESULT


class OperatorReportSchemaTests(unittest.TestCase):
    def test_valid_report_has_no_errors(self):
        data = {
            "id": "REPORT-deadbeef", "generated_at": "2026-08-06T00:00:00+00:00",
            "verification_results": [ACCEPTED_RESULT.to_dict()],
            "export_manifests": [SAMPLE_EXPORT_MANIFEST.to_dict()],
            "finishing_results": [SAMPLE_FINISHING_RESULT.to_dict()],
        }
        self.assertEqual(validate_operator_report_schema(data), [])

    def test_empty_lists_are_valid(self):
        data = {"id": "REPORT-deadbeef", "generated_at": "2026-08-06T00:00:00+00:00"}
        self.assertEqual(validate_operator_report_schema(data), [])

    def test_malformed_id_is_rejected(self):
        data = {"id": "not-a-report-id", "generated_at": "2026-08-06T00:00:00+00:00"}
        errors = validate_operator_report_schema(data)
        self.assertTrue(any("id" in e for e in errors))

    def test_bad_nested_export_manifest_is_reported_with_its_path(self):
        bad_manifest = dict(SAMPLE_EXPORT_MANIFEST.to_dict(), clips=[])
        data = {
            "id": "REPORT-deadbeef", "generated_at": "2026-08-06T00:00:00+00:00",
            "export_manifests": [bad_manifest],
        }
        errors = validate_operator_report_schema(data)
        self.assertTrue(any(e.startswith("export_manifests[0]:") for e in errors))


if __name__ == "__main__":
    unittest.main()
