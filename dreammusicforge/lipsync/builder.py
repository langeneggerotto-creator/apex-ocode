"""build_lip_sync_request()/apply_lip_sync(): turns a Shot that requires
lip sync plus its accepted Candidate and the canonical MasterSong into a
typed, evidence-backed LipSyncRequest (real ffmpeg audio extraction),
then runs it through a LipSyncAdapter (Release 0.12 ships only
NullLipSyncAdapter, see adapter.py).

Fails closed: build_lip_sync_request() refuses a shot whose
requirements.lip_sync_required is False -- building a request for a
shot that doesn't need one would silently invite a caller to apply lip
sync where it was never asked for.
"""
from __future__ import annotations

from pathlib import Path

from ..generation.models import Candidate
from ..music.models import MasterSong
from ..production.models import Shot
from .adapter import LipSyncAdapter
from .errors import LipSyncError
from .ffmpeg_runner import run_ffmpeg_extract_audio_window
from .ids import generate_lip_sync_request_id
from .models import LipSyncRequest, LipSyncResult
from .schema import validate_lip_sync_request_schema


def build_lip_sync_request(
    shot: Shot,
    candidate: Candidate,
    master_song: MasterSong,
    work_dir: Path,
    request_id: str | None = None,
) -> LipSyncRequest:
    if not shot.requirements.lip_sync_required:
        raise LipSyncError([
            f"shot {shot.id!r} does not require lip sync (requirements.lip_sync_required is False) "
            "-- refusing to build a lip-sync request for it"
        ])

    work_dir.mkdir(parents=True, exist_ok=True)
    audio_window_path = work_dir / f"{shot.id}-lipsync-audio.wav"
    run_ffmpeg_extract_audio_window(
        Path(master_song.source_file), shot.timing.start_seconds, shot.timing.end_seconds, audio_window_path,
    )

    request = LipSyncRequest(
        id=request_id or generate_lip_sync_request_id(),
        shot_id=shot.id,
        candidate_id=candidate.id,
        source_file=candidate.file,
        audio_window_file=str(audio_window_path),
        audio_start_seconds=shot.timing.start_seconds,
        audio_end_seconds=shot.timing.end_seconds,
    )

    errors = validate_lip_sync_request_schema(request.to_dict())
    if errors:
        raise LipSyncError(errors)
    return request


def apply_lip_sync(request: LipSyncRequest, adapter: LipSyncAdapter) -> LipSyncResult:
    return adapter.apply(request)
