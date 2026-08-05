"""compare_seam(): real seam comparison via ffmpeg's `ssim` filter -- the
"seam comparison" deliverable (spec section 19), covering spec section
9.2's boundary check "previous end frame to next start frame" /
"visual similarity."

SSIM_SIMILARITY_THRESHOLD is this release's own choice (0.85 on SSIM's
0-1 scale, where 1.0 is pixel-identical) -- the spec requires the check
exist but gives no numeric threshold anywhere. 0.85 is a conventional
"visually similar, not identical" cutoff for SSIM; a later release with
real accepted/rejected seam examples to calibrate against could tune it.
"""
from __future__ import annotations

from pathlib import Path

from .ffmpeg_runner import run_ffmpeg_ssim
from .models import SeamComparison

SSIM_SIMILARITY_THRESHOLD = 0.85


def compare_seam(end_frame_path: Path, start_frame_path: Path) -> SeamComparison:
    ssim_score = run_ffmpeg_ssim(end_frame_path, start_frame_path)
    return SeamComparison(ssim_score=ssim_score, similar=ssim_score >= SSIM_SIMILARITY_THRESHOLD)
