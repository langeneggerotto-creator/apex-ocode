from __future__ import annotations

import unittest

from dreammusicforge.capability_atlas.models import (
    ProviderFitReport, RendererCapability, RendererCapabilityProfile, ShotFitScore,
)

CAPABILITY_DATA = {"name": "lip_sync", "status": "measured", "evidence": "benchmarked on 40 clips"}

PROFILE_DATA = {
    "provider": "kling",
    "max_duration_seconds": 15.0,
    "max_character_count": 3,
    "supported_camera_motions": ["slow_push", "static"],
    "capabilities": [CAPABILITY_DATA],
}

SCORE_DATA = {
    "provider": "kling", "shot_id": "SHOT-deadbeef", "disqualified": False,
    "disqualification_reasons": [], "capability_scores": {"identity": 100.0}, "overall_score": 100.0,
}

REPORT_DATA = {"shot_id": "SHOT-deadbeef", "scores": [SCORE_DATA], "recommended_provider": "kling"}


class RendererCapabilityRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        capability = RendererCapability.from_dict(CAPABILITY_DATA)
        self.assertEqual(capability.to_dict(), CAPABILITY_DATA)

    def test_missing_evidence_defaults_to_none(self):
        data = {k: v for k, v in CAPABILITY_DATA.items() if k != "evidence"}
        capability = RendererCapability.from_dict(data)
        self.assertIsNone(capability.evidence)

    def test_capability_is_frozen(self):
        capability = RendererCapability.from_dict(CAPABILITY_DATA)
        with self.assertRaises(Exception):
            capability.status = "verified"  # type: ignore[misc]


class RendererCapabilityProfileRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        profile = RendererCapabilityProfile.from_dict(PROFILE_DATA)
        self.assertEqual(profile.to_dict(), PROFILE_DATA)

    def test_missing_capabilities_defaults_to_empty_tuple(self):
        data = {k: v for k, v in PROFILE_DATA.items() if k != "capabilities"}
        profile = RendererCapabilityProfile.from_dict(data)
        self.assertEqual(profile.capabilities, ())


class ShotFitScoreRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        score = ShotFitScore.from_dict(SCORE_DATA)
        self.assertEqual(score.to_dict(), SCORE_DATA)


class ProviderFitReportRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        report = ProviderFitReport.from_dict(REPORT_DATA)
        self.assertEqual(report.to_dict(), REPORT_DATA)

    def test_report_is_frozen(self):
        report = ProviderFitReport.from_dict(REPORT_DATA)
        with self.assertRaises(Exception):
            report.recommended_provider = "veo"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
