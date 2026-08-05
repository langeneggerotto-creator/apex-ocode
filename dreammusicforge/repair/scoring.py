"""score_technical_report(): turns a Release 0.9 TechnicalReport into
the 0-100 named metrics this release's thresholds/classification work
on -- the automated half of spec section 6.11's `metrics` dict.

Only metrics this repository can actually measure are produced. Section
6.11's worked example also shows `identity`/`hair`/`costume`/`world`/
`camera`/`lip_sync` metrics -- those need face embedding similarity,
costume feature matching, and the other model-assisted or manual checks
spec section 9.3 explicitly defers ("Initially support adapter
interfaces and manual scoring. Later add: face embedding similarity...").
This release doesn't have that adapter yet, so those six metrics are
never fabricated here -- `evaluate_candidate()` in repair/builder.py
accepts them as an optional, separately-supplied dict instead, which is
exactly section 9.3's "manual scoring" path.
"""
from __future__ import annotations

from ..verification.models import TechnicalReport

COLOR_SHIFT_METRIC_CEILING = 100.0


def score_technical_report(report: TechnicalReport) -> dict[str, float]:
    metrics: dict[str, float] = {
        "duration_frame_rate": 100.0 if report.duration_frame_rate_check.within_tolerance else 0.0,
    }

    if report.audio_rms is not None:
        metrics["audio"] = 0.0 if report.audio_rms.silent else 100.0
    elif any(failure.startswith("audio: expected but missing") for failure in report.failures):
        metrics["audio"] = 0.0

    if report.seam_comparison is not None:
        metrics["continuity"] = report.seam_comparison.ssim_score * 100.0

    if report.color_shift is not None:
        max_delta = max(report.color_shift.delta_y, report.color_shift.delta_u, report.color_shift.delta_v)
        metrics["color_continuity"] = max(0.0, COLOR_SHIFT_METRIC_CEILING - max_delta)

    return metrics
