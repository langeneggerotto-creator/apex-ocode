"""assemble_film(): the top-level orchestration -- this release's
acceptance test from spec section 19: "accepted shots assemble into one
video with uninterrupted song."

Every accepted candidate is normalized to one common resolution/frame
rate (clip normalization), concatenated in chronological shot order
(chronological assembly), then has its audio replaced end to end by the
canonical MasterSong -- never by whatever audio each individual clip
happened to carry (spec Law 3.9, "master audio remains external"; Law
3.2, "music is the master clock"). That's a deliberate improvement over
naive stitching: concatenating each clip's own audio track produces a
song that resets or jumps at every cut, which is not what "uninterrupted
song" means here -- one continuous pull from the master audio file is.

Fails closed at every stage: a candidate whose VerificationResult wasn't
"accept" (Release 0.10), or whose candidate_id doesn't match its own
result, never reaches ffmpeg. A requested Transition whose type isn't
actually executed by this release (see models.py's
EXECUTABLE_TRANSITION_TYPES) raises rather than silently falling back to
a hard cut without saying so -- claiming an unexecuted transition would
violate spec section 22's rule against claiming integrations that
weren't run.
"""
from __future__ import annotations

from pathlib import Path

from ..core.hashing import hash_file
from ..generation.models import Candidate
from ..music.models import MasterSong
from ..production.models import Shot
from ..repair.models import VerificationResult
from ..verification.inspector import inspect_media
from .errors import AssemblyError
from .ids import generate_export_id
from .models import AssembledClip, EXECUTABLE_TRANSITION_TYPES, ExportManifest, Transition
from .pipeline import concatenate_clips, normalize_clip, replace_audio
from .schema import validate_export_manifest_schema


def assemble_film(
    master_song: MasterSong,
    accepted: tuple[tuple[Candidate, VerificationResult], ...],
    shots_by_candidate_id: dict[str, Shot],
    output_width: int,
    output_height: int,
    output_frame_rate: float,
    work_dir: Path,
    output_path: Path,
    created_at: str,
    transitions: tuple[Transition, ...] = (),
    manifest_id: str | None = None,
) -> ExportManifest:
    errors: list[str] = []
    for candidate, result in accepted:
        if result.candidate_id != candidate.id:
            errors.append(f"VerificationResult {result.candidate_id!r} does not belong to candidate {candidate.id!r}")
        elif result.decision != "accept":
            errors.append(f"candidate {candidate.id!r} has decision {result.decision!r}, not 'accept' -- rejected candidates cannot be assembled")
        if candidate.id not in shots_by_candidate_id:
            errors.append(f"candidate {candidate.id!r} has no corresponding shot in shots_by_candidate_id")
    for transition in transitions:
        if transition.transition_type not in EXECUTABLE_TRANSITION_TYPES:
            errors.append(
                f"transition_type {transition.transition_type!r} is not executed by this release "
                f"(only {EXECUTABLE_TRANSITION_TYPES} are) -- refusing to silently fall back to a hard cut"
            )
    if errors:
        raise AssemblyError(errors)

    ordered = sorted(accepted, key=lambda pair: shots_by_candidate_id[pair[0].id].timing.start_seconds)

    work_dir.mkdir(parents=True, exist_ok=True)
    normalized_paths: list[Path] = []
    normalized_durations: list[float] = []
    for candidate, _ in ordered:
        normalized_path = work_dir / f"{candidate.id}-normalized.mp4"
        normalize_clip(Path(candidate.file), normalized_path, output_width, output_height, output_frame_rate)
        normalized_paths.append(normalized_path)
        normalized_durations.append(inspect_media(normalized_path).duration_seconds)

    concatenated_path = work_dir / "concatenated-video-only.mp4"
    concatenate_clips(tuple(normalized_paths), concatenated_path)
    total_duration_seconds = inspect_media(concatenated_path).duration_seconds

    replace_audio(concatenated_path, Path(master_song.source_file), output_path, total_duration_seconds)

    start_seconds = 0.0
    clips: list[AssembledClip] = []
    for (candidate, _), duration in zip(ordered, normalized_durations):
        clips.append(AssembledClip(
            candidate_id=candidate.id, shot_id=shots_by_candidate_id[candidate.id].id,
            source_hash=candidate.output_hash, start_seconds_in_final=start_seconds,
            normalized_duration_seconds=duration,
        ))
        start_seconds += duration

    manifest = ExportManifest(
        id=manifest_id or generate_export_id(),
        master_song_id=master_song.id,
        master_song_hash=master_song.hash,
        output_file=str(output_path),
        output_hash=hash_file(output_path),
        total_duration_seconds=total_duration_seconds,
        created_at=created_at,
        clips=tuple(clips),
        transitions=transitions,
    )

    validation_errors = validate_export_manifest_schema(manifest.to_dict())
    if validation_errors:
        raise AssemblyError(validation_errors)
    return manifest
