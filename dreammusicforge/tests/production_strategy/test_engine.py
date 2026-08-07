import pytest

from dreammusicforge.production_strategy import (
    CapabilityProfile,
    ProductionStrategy,
    TransitionRequirements,
    choose_strategy,
)


def profile(**overrides):
    values = dict(
        renderer_id="test-renderer",
        max_duration_seconds=15.0,
        supports_start_frame=True,
        supports_end_frame=True,
        supports_motion_control=True,
        supports_character_reference=True,
        supports_multi_character=False,
        supports_native_audio=True,
        supports_lip_sync=False,
        max_reliable_characters=1,
    )
    values.update(overrides)
    return CapabilityProfile(**values)


def req(**overrides):
    values = dict(transition_id="T-001", duration_seconds=8.0)
    values.update(overrides)
    return TransitionRequirements(**values)


def test_simple_shot_direct_render():
    assert choose_strategy(req(), profile()).strategy is ProductionStrategy.DIRECT_RENDER


def test_long_continuous_take_uses_controlled_continuation():
    decision = choose_strategy(
        req(duration_seconds=24.0, continuous_take_required=True),
        profile(),
    )
    assert decision.strategy is ProductionStrategy.CONTROLLED_CONTINUATION
    assert "export_verified_end_frame" in decision.mitigations


def test_large_ensemble_layers_when_allowed():
    decision = choose_strategy(req(character_count=7), profile(max_reliable_characters=2))
    assert decision.strategy is ProductionStrategy.LAYERED_COMPOSITING


def test_extreme_choreography_layers():
    decision = choose_strategy(req(choreography_complexity=3), profile())
    assert decision.strategy is ProductionStrategy.LAYERED_COMPOSITING


def test_missing_native_lipsync_routes_to_specialist():
    decision = choose_strategy(req(lip_sync_required=True), profile(supports_lip_sync=False))
    assert decision.strategy is ProductionStrategy.EXTERNAL_SPECIALIST_STAGE


def test_missing_identity_reference_fails_closed():
    decision = choose_strategy(
        req(exact_identity_required=True, external_specialist_available=False),
        profile(supports_character_reference=False),
    )
    assert decision.strategy is ProductionStrategy.REDESIGN_REQUIRED


def test_invalid_requirements_rejected():
    with pytest.raises(ValueError):
        choose_strategy(req(duration_seconds=0), profile())


def test_long_noncontinuous_shot_uses_editorial_illusion():
    decision = choose_strategy(req(duration_seconds=25.0), profile())
    assert decision.strategy is ProductionStrategy.EDITORIAL_ILLUSION
