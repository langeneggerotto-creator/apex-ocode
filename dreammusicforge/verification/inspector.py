"""inspect_media(): real media inspection via ffprobe -- the "media
inspection" deliverable (spec section 19), covering spec section 9.1's
"file readable," "duration," "frame rate," "resolution," "codec," and
"audio presence" technical checks.
"""
from __future__ import annotations

from pathlib import Path

from .errors import FfmpegRunError
from .ffmpeg_runner import run_ffprobe_json
from .models import MediaMetadata


def _parse_frame_rate(raw: str) -> float:
    if "/" not in raw:
        return float(raw)
    numerator, denominator = raw.split("/", 1)
    denominator_value = float(denominator)
    if denominator_value == 0:
        return 0.0
    return float(numerator) / denominator_value


def inspect_media(file_path: Path) -> MediaMetadata:
    probe = run_ffprobe_json(file_path)

    streams = probe.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]

    if not video_streams:
        raise FfmpegRunError([f"{file_path} has no video stream"])
    video = video_streams[0]

    format_info = probe.get("format", {})
    try:
        duration_seconds = float(format_info.get("duration") or video.get("duration"))
    except (TypeError, ValueError) as exc:
        raise FfmpegRunError([f"{file_path} reports no readable duration"]) from exc

    has_audio = bool(audio_streams)
    audio_codec = audio_streams[0].get("codec_name") if has_audio else None

    return MediaMetadata(
        duration_seconds=duration_seconds,
        frame_rate=_parse_frame_rate(video.get("r_frame_rate", "0/1")),
        width=int(video["width"]),
        height=int(video["height"]),
        video_codec=video.get("codec_name", "unknown"),
        has_audio=has_audio,
        audio_codec=audio_codec,
    )
