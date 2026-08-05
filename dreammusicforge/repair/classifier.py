"""Critical thresholds, failure classification, and repair
recommendations -- three of this release's four "Build" deliverables
(spec section 19); `builder.py`'s accept/reject workflow is the fourth.

DEFAULT_CRITICAL_THRESHOLDS and METRIC_RECOMMENDATIONS are this
release's own numbers and defaults -- the spec requires the thresholds
and recommendation mechanism exist (sections 19, 8.9, 8.10) but gives
no numeric cutoffs anywhere, and 8.10's ranking rule ("a beautiful
candidate with a critical continuity failure must rank below a less
beautiful candidate that preserves the canonical film") is qualitative,
not numeric. METRIC_RECOMMENDATIONS is seeded from section 8.9's six
named concealment actions, plus `lip_sync` mapping to
`dedicated_lip_sync_pass` -- section 6.11's own worked example for
exactly that failure, reused rather than reinvented. Both are
overridable per call; nothing here is a closed enum a caller can't
extend (see models.py's module docstring for why `REPAIR_ACTIONS` isn't
a schema-enforced closed list either).
"""
from __future__ import annotations

from .ids import generate_defect_id
from .models import Defect

DEFAULT_CRITICAL_THRESHOLDS: dict[str, float] = {
    "duration_frame_rate": 50.0,
    "audio": 50.0,
    "continuity": 70.0,
    "color_continuity": 50.0,
    "identity": 90.0,
    "hair": 90.0,
    "costume": 90.0,
    "world": 90.0,
    "camera": 80.0,
    "lip_sync": 80.0,
}
DEFAULT_THRESHOLD_FOR_UNLISTED_METRICS = 70.0

METRIC_RECOMMENDATIONS: dict[str, tuple[str, ...]] = {
    "duration_frame_rate": ("shorten_shot", "regenerate"),
    "audio": ("regenerate",),
    "continuity": ("regenerate", "cut_away_before_defect"),
    "color_continuity": ("use_light_flash", "replace_local_region", "regenerate"),
    "identity": ("regenerate",),
    "hair": ("regenerate",),
    "costume": ("regenerate",),
    "world": ("regenerate",),
    "camera": ("replace_local_region", "regenerate"),
    "lip_sync": ("dedicated_lip_sync_pass", "regenerate"),
}
DEFAULT_RECOMMENDATIONS_FOR_UNLISTED_METRICS = ("regenerate",)


def _severity_for(score: float, threshold: float) -> str:
    if threshold <= 0:
        return "critical"
    ratio = score / threshold
    if ratio <= 0.5:
        return "critical"
    if ratio <= 0.75:
        return "high"
    return "medium"


def classify_failures(
    metrics: dict[str, float],
    shot_id: str,
    thresholds: dict[str, float] | None = None,
) -> tuple[Defect, ...]:
    """Returns one Defect per metric that falls below its critical
    threshold, ordered by ascending score (worst first)."""
    effective_thresholds = dict(DEFAULT_CRITICAL_THRESHOLDS)
    if thresholds:
        effective_thresholds.update(thresholds)

    failing = [
        (name, score, effective_thresholds.get(name, DEFAULT_THRESHOLD_FOR_UNLISTED_METRICS))
        for name, score in metrics.items()
        if score < effective_thresholds.get(name, DEFAULT_THRESHOLD_FOR_UNLISTED_METRICS)
    ]
    failing.sort(key=lambda item: item[1])

    return tuple(
        Defect(
            id=generate_defect_id(), type=name, severity=_severity_for(score, threshold), shot_id=shot_id,
            recommendations=METRIC_RECOMMENDATIONS.get(name, DEFAULT_RECOMMENDATIONS_FOR_UNLISTED_METRICS),
        )
        for name, score, threshold in failing
    )
