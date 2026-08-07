from dreammusicforge.production_strategy.models import (
    CapabilityProfile,
    ProductionRisk,
    ProductionStrategy,
    StrategyDecision,
    TransitionRequirements,
)
from dreammusicforge.providers.kling.compiler import KlingCreativeContract, compile_kling_package
from dreammusicforge.providers.kling.models import KlingMode


def capability(**overrides):
    data = dict(
        renderer_id="kling-video-current",
        max_duration_seconds=15.0,
        supports_start_frame=True,
        supports_end_frame=True,
        supports_motion_control=True,
        supports_character_reference=True,
        supports_multi_character=True,
        supports_native_audio=True,
        supports_lip_sync=False,
        max_reliable_characters=2,
    )
    data.update(overrides)
    return CapabilityProfile(**data)


def contract(**overrides):
    data = dict(
        performer_id="PERFORMER-001",
        costume_id="COSTUME-001",
        world_id="WORLD-001",
        action="sing while stepping toward camera",
        camera="50mm slow push-in",
        lighting="cool blue key with warm rim",
        emotion="growing connection",
        song_interval="00:10.000-00:18.000",
        start_frame_id="FRAME-START-001",
        character_reference_id="CHAR-001",
        world_reference_id="WORLD-REF-001",
        costume_reference_id="COSTUME-REF-001",
    )
    data.update(overrides)
    return KlingCreativeContract(**data)


def decision(strategy=ProductionStrategy.DIRECT_RENDER, risk=ProductionRisk.LOW):
    return StrategyDecision("TR-001", strategy, risk, ("reason",), ("fallback",))


def requirements(**overrides):
    data = dict(transition_id="TR-001", duration_seconds=8.0)
    data.update(overrides)
    return TransitionRequirements(**data)


def test_direct_render_compiles_image_to_video_when_start_frame_exists():
    package = compile_kling_package(decision(), requirements(), capability(), contract())
    assert package.mode is KlingMode.IMAGE_TO_VIDEO
    assert package.requires_external_master_audio is True
    assert "identity" in package.acceptance_gates


def test_controlled_continuation_requires_start_frame_support():
    try:
        compile_kling_package(
            decision(ProductionStrategy.CONTROLLED_CONTINUATION, ProductionRisk.MEDIUM),
            requirements(duration_seconds=20.0, continuous_take_required=True),
            capability(supports_start_frame=False),
            contract(),
        )
    except ValueError as exc:
        assert "start-frame" in str(exc)
    else:
        raise AssertionError("expected controlled continuation to fail closed")


def test_controlled_continuation_caps_single_segment_to_renderer_limit():
    package = compile_kling_package(
        decision(ProductionStrategy.CONTROLLED_CONTINUATION, ProductionRisk.MEDIUM),
        requirements(duration_seconds=24.0, continuous_take_required=True),
        capability(),
        contract(),
    )
    assert package.mode is KlingMode.START_FRAME_CONTINUATION
    assert package.duration_seconds == 15.0
    assert "state_continuity" in package.acceptance_gates


def test_layered_compositing_compiles_layer_pass():
    package = compile_kling_package(
        decision(ProductionStrategy.LAYERED_COMPOSITING, ProductionRisk.HIGH),
        requirements(character_count=7, choreography_complexity=3),
        capability(),
        contract(),
    )
    assert package.mode is KlingMode.LAYERED_PASS
    assert package.candidate_count == 4


def test_unsupported_lip_sync_routes_external_lip_sync_flag():
    package = compile_kling_package(
        decision(ProductionStrategy.EXTERNAL_SPECIALIST_STAGE, ProductionRisk.HIGH),
        requirements(lip_sync_required=True),
        capability(supports_lip_sync=False),
        contract(),
    )
    assert package.mode is KlingMode.EXTERNAL_STAGE
    assert package.requires_external_lip_sync is True


def test_direct_render_rejects_duration_above_capability():
    try:
        compile_kling_package(decision(), requirements(duration_seconds=16.0), capability(), contract())
    except ValueError as exc:
        assert "maximum duration" in str(exc)
    else:
        raise AssertionError("expected direct render to fail closed")


def test_non_kling_profile_rejected():
    try:
        compile_kling_package(decision(), requirements(), capability(renderer_id="veo-current"), contract())
    except ValueError as exc:
        assert "Kling" in str(exc)
    else:
        raise AssertionError("expected non-Kling capability profile rejection")


def test_package_preserves_canonical_master_audio_rule():
    package = compile_kling_package(decision(), requirements(), capability(), contract())
    assert package.requires_external_master_audio is True
    assert "external canonical master song" in package.prompt
