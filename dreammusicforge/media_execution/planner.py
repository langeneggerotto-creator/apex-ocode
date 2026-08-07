from __future__ import annotations

from pathlib import PurePosixPath

from dreammusicforge.assembly.models import AssemblyManifest, TransitionType
from .models import MediaExecutionPlan, MediaExecutionStep


def _safe_name(name: str) -> str:
    if not name.strip() or name != PurePosixPath(name).name:
        raise ValueError("media execution only accepts simple file names")
    return name


def compile_media_execution_plan(manifest: AssemblyManifest) -> MediaExecutionPlan:
    manifest.validate()
    if not manifest.mute_provider_audio:
        raise ValueError("v0.1 requires provider audio to be muted")
    if any(t.transition_type is not TransitionType.CUT for t in manifest.transitions):
        raise ValueError("v0.1 execution supports CUT transitions only")

    steps: list[MediaExecutionStep] = []
    normalized: list[str] = []
    n = manifest.normalization

    for index, asset in enumerate(manifest.assets, start=1):
        src = _safe_name(asset.file_name)
        out = f"normalized_{index:04d}.mp4"
        normalized.append(out)
        steps.append(MediaExecutionStep(
            step_id=f"normalize-{index:04d}",
            operation="NORMALIZE_VIDEO",
            command=(
                "ffmpeg", "-y", "-i", src, "-an",
                "-vf", f"scale={n.width}:{n.height}:force_original_aspect_ratio=decrease,pad={n.width}:{n.height}:(ow-iw)/2:(oh-ih)/2,fps={n.fps}",
                "-c:v", n.video_codec, "-pix_fmt", n.pixel_format, out,
            ),
            inputs=(src,), outputs=(out,),
        ))

    concat_file = "concat.txt"
    silent_video = "assembled_silent.mp4"
    steps.append(MediaExecutionStep(
        step_id="concat-video",
        operation="CONCAT_VIDEO",
        command=("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", silent_video),
        inputs=tuple(normalized) + (concat_file,), outputs=(silent_video,),
    ))

    master = _safe_name(manifest.master_audio.file_name)
    final_out = _safe_name(manifest.output_file_name)
    offset = manifest.master_audio.start_offset_seconds
    steps.append(MediaExecutionStep(
        step_id="master-audio-layback",
        operation="MASTER_AUDIO_LAYBACK",
        command=(
            "ffmpeg", "-y", "-i", silent_video,
            "-ss", f"{offset:.6f}", "-i", master,
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", final_out,
        ),
        inputs=(silent_video, master), outputs=(final_out,),
    ))

    plan = MediaExecutionPlan(
        plan_id=f"MEDIA-{manifest.manifest_id}",
        manifest_id=manifest.manifest_id,
        steps=tuple(steps),
        final_output_file=final_out,
        master_audio_file=master,
        mute_provider_audio=True,
    )
    plan.validate()
    return plan
