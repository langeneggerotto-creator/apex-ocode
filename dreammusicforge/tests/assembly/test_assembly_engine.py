import pytest

from dreammusicforge.assembly import (
    AcceptedAsset,
    MasterAudioContract,
    NormalizationTarget,
    TransitionContract,
    TransitionType,
    compile_assembly_manifest,
)


def asset(candidate_id: str, start: float, end: float) -> AcceptedAsset:
    return AcceptedAsset(
        candidate_id=candidate_id,
        file_name=f"{candidate_id}.mp4",
        sha256=f"sha-{candidate_id}",
        start_seconds=start,
        end_seconds=end,
        width=1080,
        height=1920,
        fps=30.0,
    )


def master_audio(duration: float = 30.0) -> MasterAudioContract:
    return MasterAudioContract("song.wav", "sha-song", duration)


def target() -> NormalizationTarget:
    return NormalizationTarget(1080, 1920, 30.0)


def test_compiles_ordered_manifest_and_mutes_provider_audio():
    a = asset("A", 0, 5)
    b = asset("B", 5, 10)
    transition = TransitionContract("A", "B", TransitionType.CUT)
    manifest = compile_assembly_manifest(
        manifest_id="M1",
        assets=(b, a),
        transitions=(transition,),
        master_audio=master_audio(),
        normalization=target(),
        output_file_name="final.mp4",
    )
    assert [item.candidate_id for item in manifest.assets] == ["A", "B"]
    assert manifest.mute_provider_audio is True
    assert len(manifest.seams) == 1


def test_rejects_timeline_gap():
    with pytest.raises(ValueError, match="exactly cover"):
        compile_assembly_manifest(
            manifest_id="M1",
            assets=(asset("A", 0, 5), asset("B", 6, 10)),
            transitions=(TransitionContract("A", "B", TransitionType.CUT),),
            master_audio=master_audio(),
            normalization=target(),
            output_file_name="final.mp4",
        )


def test_rejects_timeline_overlap():
    with pytest.raises(ValueError, match="overlap"):
        compile_assembly_manifest(
            manifest_id="M1",
            assets=(asset("A", 0, 5), asset("B", 4, 10)),
            transitions=(TransitionContract("A", "B", TransitionType.CUT),),
            master_audio=master_audio(),
            normalization=target(),
            output_file_name="final.mp4",
        )


def test_requires_transition_for_every_adjacent_pair():
    with pytest.raises(ValueError, match="transition contracts"):
        compile_assembly_manifest(
            manifest_id="M1",
            assets=(asset("A", 0, 5), asset("B", 5, 10)),
            transitions=(),
            master_audio=master_audio(),
            normalization=target(),
            output_file_name="final.mp4",
        )


def test_rejects_unrelated_transition_pair():
    with pytest.raises(ValueError, match="transition contracts"):
        compile_assembly_manifest(
            manifest_id="M1",
            assets=(asset("A", 0, 5), asset("B", 5, 10)),
            transitions=(TransitionContract("B", "A", TransitionType.CUT),),
            master_audio=master_audio(),
            normalization=target(),
            output_file_name="final.mp4",
        )


def test_rejects_master_audio_shorter_than_film():
    with pytest.raises(ValueError, match="master audio"):
        compile_assembly_manifest(
            manifest_id="M1",
            assets=(asset("A", 0, 5), asset("B", 5, 10)),
            transitions=(TransitionContract("A", "B", TransitionType.CUT),),
            master_audio=master_audio(9.0),
            normalization=target(),
            output_file_name="final.mp4",
        )


def test_cut_must_have_zero_duration():
    with pytest.raises(ValueError, match="hard cut"):
        TransitionContract("A", "B", TransitionType.CUT, 0.5).validate()


def test_single_asset_requires_no_transition():
    manifest = compile_assembly_manifest(
        manifest_id="M1",
        assets=(asset("A", 0, 5),),
        transitions=(),
        master_audio=master_audio(),
        normalization=target(),
        output_file_name="final.mp4",
    )
    assert manifest.transitions == ()
    assert manifest.seams == ()
