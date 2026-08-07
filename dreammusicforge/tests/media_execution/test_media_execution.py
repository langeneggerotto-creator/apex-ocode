from pathlib import Path

import pytest

from dreammusicforge.assembly.models import (
    AcceptedAsset, AssemblyManifest, MasterAudioContract, NormalizationTarget,
    SeamRecord, TransitionContract, TransitionType,
)
from dreammusicforge.media_execution import compile_media_execution_plan, execute_media_plan, ExecutionStatus


def manifest(transition=TransitionType.CUT, mute=True):
    assets = (
        AcceptedAsset("A", "a.mp4", "a" * 64, 0.0, 5.0, 512, 910, 30.0),
        AcceptedAsset("B", "b.mp4", "b" * 64, 5.0, 10.0, 512, 910, 30.0),
    )
    transitions = (TransitionContract("A", "B", transition, 0.0 if transition is TransitionType.CUT else 0.5),)
    seams = (SeamRecord("A", "B", 5.0, 5.0, transition, True),)
    return AssemblyManifest(
        "M1", assets, transitions,
        MasterAudioContract("song.wav", "c" * 64, 10.0),
        NormalizationTarget(512, 910, 30.0), seams, mute, "final.mp4"
    )


def test_compiles_normalize_concat_and_audio_steps():
    plan = compile_media_execution_plan(manifest())
    assert [s.operation for s in plan.steps] == ["NORMALIZE_VIDEO", "NORMALIZE_VIDEO", "CONCAT_VIDEO", "MASTER_AUDIO_LAYBACK"]


def test_provider_audio_is_removed_during_normalization():
    plan = compile_media_execution_plan(manifest())
    assert "-an" in plan.steps[0].command


def test_master_audio_is_final_authority():
    plan = compile_media_execution_plan(manifest())
    assert plan.master_audio_file == "song.wav"
    assert "song.wav" in plan.steps[-1].inputs


def test_non_cut_transition_fails_closed_in_v01():
    with pytest.raises(ValueError):
        compile_media_execution_plan(manifest(TransitionType.DISSOLVE))


def test_provider_audio_unmuted_fails_closed():
    with pytest.raises(ValueError):
        compile_media_execution_plan(manifest(mute=False))


def test_path_traversal_fails_closed():
    m = manifest()
    bad = AssemblyManifest(m.manifest_id, (AcceptedAsset("A", "../a.mp4", "a" * 64, 0, 5, 512, 910, 30),), (), m.master_audio, m.normalization, (), True, "final.mp4")
    with pytest.raises(ValueError):
        compile_media_execution_plan(bad)


def test_dry_run_is_planned(tmp_path: Path):
    evidence = execute_media_plan(compile_media_execution_plan(manifest()), tmp_path, dry_run=True)
    assert evidence.status is ExecutionStatus.PLANNED
    assert len(evidence.executed_steps) == 4


def test_plan_is_provider_neutral_after_assembly():
    plan = compile_media_execution_plan(manifest())
    assert all("kling" not in " ".join(step.command).lower() for step in plan.steps)
