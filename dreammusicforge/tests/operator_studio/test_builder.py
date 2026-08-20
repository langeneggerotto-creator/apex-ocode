from __future__ import annotations

import unittest

from dreammusicforge.operator_studio.builder import build_operator_report
from dreammusicforge.operator_studio.errors import OperatorStudioError

from .sample_data import ACCEPTED_RESULT, REJECTED_RESULT, SAMPLE_EXPORT_MANIFEST, SAMPLE_FINISHING_RESULT


class BuildOperatorReportTests(unittest.TestCase):
    def test_builds_a_valid_report(self):
        report = build_operator_report(
            verification_results=(ACCEPTED_RESULT, REJECTED_RESULT),
            export_manifests=(SAMPLE_EXPORT_MANIFEST,),
            finishing_results=(SAMPLE_FINISHING_RESULT,),
            generated_at="2026-08-06T00:00:00+00:00",
        )
        self.assertTrue(report.id.startswith("REPORT-"))
        self.assertEqual(len(report.verification_results), 2)
        self.assertEqual(len(report.export_manifests), 1)
        self.assertEqual(len(report.finishing_results), 1)

    def test_empty_report_is_valid(self):
        report = build_operator_report(generated_at="2026-08-06T00:00:00+00:00")
        self.assertEqual(report.verification_results, ())

    def test_invalid_nested_verification_result_raises(self):
        import dataclasses
        bad_result = dataclasses.replace(ACCEPTED_RESULT, decision="maybe")
        with self.assertRaises(OperatorStudioError):
            build_operator_report(verification_results=(bad_result,), generated_at="2026-08-06T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
