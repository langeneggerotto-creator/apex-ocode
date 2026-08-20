from __future__ import annotations

import unittest

from dreammusicforge.operator_studio.builder import build_operator_report
from dreammusicforge.operator_studio.render import render_report_html

from .sample_data import ACCEPTED_RESULT, REJECTED_RESULT, SAMPLE_EXPORT_MANIFEST, SAMPLE_FINISHING_RESULT


class RenderReportHtmlTests(unittest.TestCase):
    def setUp(self):
        self.report = build_operator_report(
            verification_results=(ACCEPTED_RESULT, REJECTED_RESULT),
            export_manifests=(SAMPLE_EXPORT_MANIFEST,),
            finishing_results=(SAMPLE_FINISHING_RESULT,),
            generated_at="2026-08-06T00:00:00+00:00",
        )
        self.html = render_report_html(self.report)

    def test_produces_a_complete_html_document(self):
        self.assertIn("<!doctype html>", self.html.lower())
        self.assertIn("</html>", self.html.lower())

    def test_includes_accepted_and_rejected_candidates(self):
        self.assertIn("CANDIDATE-accepted", self.html)
        self.assertIn("CANDIDATE-rejected", self.html)
        self.assertIn("regenerate", self.html)  # the repair action

    def test_includes_export_and_finishing_data(self):
        self.assertIn("EXPORT-deadbeef", self.html)
        self.assertIn("FINISHING-deadbeef", self.html)

    def test_escapes_hostile_candidate_id(self):
        import dataclasses
        hostile = dataclasses.replace(ACCEPTED_RESULT, candidate_id="CANDIDATE-<script>alert(1)</script>")
        report = build_operator_report(verification_results=(hostile,), generated_at="2026-08-06T00:00:00+00:00")
        html = render_report_html(report)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_empty_report_renders_without_error(self):
        empty_report = build_operator_report(generated_at="2026-08-06T00:00:00+00:00")
        html = render_report_html(empty_report)
        self.assertIn("none", html)


if __name__ == "__main__":
    unittest.main()
