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
from .pipeline import concatenate_clips, concatenate_clips_with_transitions, normalize_clip, replace_audio
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
    ordered_shot_ids = [shots_by_candidate_id[candidate.id].id for candidate, _ in ordered]

    work_dir.mkdir(parents=True, exist_ok=True)
    normalized_paths: list[Path] = []
    normalized_durations: list[float] = []
    for candidate, _ in ordered:
        normalized_path = work_dir / f"{candidate.id}-normalized.mp4"
        normalize_clip(Path(candidate.file), normalized_path, output_width, output_height, output_frame_rate)
        normalized_paths.append(normalized_path)
        normalized_durations.append(inspect_media(normalized_path).duration_seconds)

    # Resolve one (transition_type, duration_seconds) per adjacent pair
    # in final chronological order, defaulting to an implicit hard cut
    # when the caller didn't declare a Transition for that pair -- this
    # preserves Release 0.11's original behavior for callers that never
    # pass `transitions` at all. Every declared Transition must land on
    # an actual adjacent pair and, if it's a dissolve, must have a
    # duration that fits inside both of its neighboring clips -- an
    # xfade offset that goes negative or exceeds either clip's own
    # length isn't executable, so it fails closed here rather than
    # producing a corrupt ffmpeg filter graph.
    transitions_by_pair = {(t.source_shot_id, t.destination_shot_id): t for t in transitions}
    pair_transitions: list[tuple[str, float]] = []
    for index in range(len(ordered) - 1):
        pair_key = (ordered_shot_ids[index], ordered_shot_ids[index + 1])
        transition = transitions_by_pair.pop(pair_key, None)
        if transition is None:
            pair_transitions.append(("hard_cut", 0.0))
            continue
        if transition.transition_type == "dissolve":
            if transition.duration_seconds <= 0:
                errors.append(f"dissolve transition {pair_key!r} must have duration_seconds > 0, got {transition.duration_seconds}")
            elif transition.duration_seconds >= normalized_durations[index] or transition.duration_seconds >= normalized_durations[index + 1]:
                errors.append(
                    f"dissolve transition {pair_key!r} duration_seconds ({transition.duration_seconds}) must be less than "
                    f"both adjacent clip durations ({normalized_durations[index]}, {normalized_durations[index + 1]})"
                )
        pair_transitions.append((transition.transition_type, transition.duration_seconds))
    if transitions_by_pair:
        errors.append(
            f"transition(s) {list(transitions_by_pair)!r} do not correspond to any adjacent pair in the final "
            "chronological order -- refusing to silently drop a declared transition"
        )
    if errors:
        raise AssemblyError(errors)

    concatenated_path = work_dir / "concatenated-video-only.mp4"
    if all(transition_type == "hard_cut" for transition_type, _ in pair_transitions):
        concatenate_clips(tuple(normalized_paths), concatenated_path)
    else:
        concatenate_clips_with_transitions(
            tuple(normalized_paths), tuple(normalized_durations), tuple(pair_transitions), output_frame_rate, concatenated_path,
        )
    total_duration_seconds = inspect_media(concatenated_path).duration_seconds

    replace_audio(concatenated_path, Path(master_song.source_file), output_path, total_duration_seconds)

    cumulative_end_seconds = 0.0
    clips: list[AssembledClip] = []
    for index, ((candidate, _), duration) in enumerate(zip(ordered, normalized_durations)):
        if index == 0:
            clip_start = 0.0
        else:
            transition_type, transition_duration = pair_transitions[index - 1]
            overlap = transition_duration if transition_type == "dissolve" else 0.0
            clip_start = cumulative_end_seconds - overlap
        clips.append(AssembledClip(
            candidate_id=candidate.id, shot_id=shots_by_candidate_id[candidate.id].id,
            source_hash=candidate.output_hash, start_seconds_in_final=clip_start,
            normalized_duration_seconds=duration,
        ))
        cumulative_end_seconds = clip_start + duration

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
