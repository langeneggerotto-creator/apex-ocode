from __future__ import annotations

from .models import (
    AcceptedAsset,
    AssemblyManifest,
    MasterAudioContract,
    NormalizationTarget,
    SeamRecord,
    TransitionContract,
)


def compile_assembly_manifest(
    *,
    manifest_id: str,
    assets: tuple[AcceptedAsset, ...],
    transitions: tuple[TransitionContract, ...],
    master_audio: MasterAudioContract,
    normalization: NormalizationTarget,
    output_file_name: str,
) -> AssemblyManifest:
    if not manifest_id.strip():
        raise ValueError("manifest_id is required")
    if not assets:
        raise ValueError("assembly requires accepted assets")

    ordered = tuple(sorted(assets, key=lambda asset: (asset.start_seconds, asset.end_seconds, asset.candidate_id)))
    for asset in ordered:
        asset.validate()

    for left, right in zip(ordered, ordered[1:]):
        if right.start_seconds < left.end_seconds:
            raise ValueError("accepted assets overlap on the canonical film timeline")
        if abs(right.start_seconds - left.end_seconds) > 1e-6:
            raise ValueError("accepted assets must exactly cover the canonical film timeline")

    expected_pairs = {(left.candidate_id, right.candidate_id) for left, right in zip(ordered, ordered[1:])}
    supplied_pairs = {(item.source_candidate_id, item.destination_candidate_id) for item in transitions}
    if expected_pairs != supplied_pairs:
        raise ValueError("transition contracts must cover every and only adjacent accepted-asset pair")

    transition_by_pair = {
        (item.source_candidate_id, item.destination_candidate_id): item
        for item in transitions
    }
    if len(transition_by_pair) != len(transitions):
        raise ValueError("duplicate transition contract")

    seams = []
    for left, right in zip(ordered, ordered[1:]):
        transition = transition_by_pair[(left.candidate_id, right.candidate_id)]
        transition.validate()
        seams.append(
            SeamRecord(
                source_candidate_id=left.candidate_id,
                destination_candidate_id=right.candidate_id,
                source_end_seconds=left.end_seconds,
                destination_start_seconds=right.start_seconds,
                transition_type=transition.transition_type,
                requires_seam_verification=True,
            )
        )

    master_audio.validate()
    normalization.validate()
    film_duration = ordered[-1].end_seconds - ordered[0].start_seconds
    audio_available = master_audio.duration_seconds - master_audio.start_offset_seconds
    if audio_available + 1e-6 < film_duration:
        raise ValueError("canonical master audio does not cover assembled film duration")

    manifest = AssemblyManifest(
        manifest_id=manifest_id,
        assets=ordered,
        transitions=transitions,
        master_audio=master_audio,
        normalization=normalization,
        seams=tuple(seams),
        mute_provider_audio=True,
        output_file_name=output_file_name,
    )
    manifest.validate()
    return manifest
