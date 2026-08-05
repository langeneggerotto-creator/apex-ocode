"""measure_color_shift(): real color-shift measurement via ffmpeg's
`signalstats` filter -- the "color shift" deliverable (spec section 19),
covering spec section 9.2's boundary checks "luminance shift" and
"color shift."

COLOR_SHIFT_THRESHOLD is this release's own choice (10.0, on
signalstats' 0-255 YUV scale) -- conventional for "a shift a viewer
would likely notice," not a spec-given number.
"""
from __future__ import annotations

from pathlib import Path

from .ffmpeg_runner import run_ffmpeg_signalstats
from .models import ColorShiftReport

COLOR_SHIFT_THRESHOLD = 10.0


def measure_color_shift(frame_a_path: Path, frame_b_path: Path) -> ColorShiftReport:
    stats_a = run_ffmpeg_signalstats(frame_a_path)
    stats_b = run_ffmpeg_signalstats(frame_b_path)

    delta_y = abs(stats_a["yavg"] - stats_b["yavg"])
    delta_u = abs(stats_a["uavg"] - stats_b["uavg"])
    delta_v = abs(stats_a["vavg"] - stats_b["vavg"])

    return ColorShiftReport(
        delta_y=delta_y, delta_u=delta_u, delta_v=delta_v,
        shifted=max(delta_y, delta_u, delta_v) >= COLOR_SHIFT_THRESHOLD,
    )
