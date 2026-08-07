from __future__ import annotations

from .models import (
    CapabilityProfile,
    ProductionRisk,
    ProductionStrategy,
    StrategyDecision,
    TransitionRequirements,
)


def _risk_from_points(points: int) -> ProductionRisk:
    if points <= 2:
        return ProductionRisk.LOW
    if points <= 5:
        return ProductionRisk.MEDIUM
    if points <= 8:
        return ProductionRisk.HIGH
    return ProductionRisk.EXTREME


def choose_strategy(
    requirements: TransitionRequirements,
    capability: CapabilityProfile,
) -> StrategyDecision:
    """Choose the safest production strategy deterministically.

    Fail closed: invalid inputs raise ValueError; unsupported critical demands
    resolve to specialist/redesign strategies rather than optimistic rendering.
    """
    requirements.validate()
    capability.validate()

    reasons: list[str] = []
    mitigations: list[str] = []
    points = 0

    exceeds_duration = requirements.duration_seconds > capability.max_duration_seconds
    exceeds_people = requirements.character_count > capability.max_reliable_characters

    if exceeds_duration:
        points += 3
        reasons.append("duration_exceeds_renderer_limit")
    if exceeds_people:
        points += 3
        reasons.append("character_count_exceeds_reliable_limit")
    if requirements.choreography_complexity >= 2:
        points += requirements.choreography_complexity
        reasons.append("complex_choreography")
    if requirements.camera_complexity >= 2:
        points += requirements.camera_complexity - 1
        reasons.append("complex_camera_motion")
    if requirements.hand_object_interaction:
        points += 2
        reasons.append("hand_object_interaction")
    if requirements.lip_sync_required and not capability.supports_lip_sync:
        points += 2
        reasons.append("lip_sync_not_native")
    if requirements.exact_identity_required and not capability.supports_character_reference:
        points += 3
        reasons.append("critical_identity_reference_unsupported")

    risk = _risk_from_points(points)

    # Critical unsupported identity must not be rendered optimistically.
    if requirements.exact_identity_required and not capability.supports_character_reference:
        if requirements.external_specialist_available:
            mitigations.append("use_external_identity_or_compositing_stage")
            return StrategyDecision(
                requirements.transition_id,
                ProductionStrategy.EXTERNAL_SPECIALIST_STAGE,
                ProductionRisk.EXTREME,
                tuple(reasons),
                tuple(mitigations),
            )
        return StrategyDecision(
            requirements.transition_id,
            ProductionStrategy.REDESIGN_REQUIRED,
            ProductionRisk.EXTREME,
            tuple(reasons),
            ("redesign_identity_critical_shot",),
        )

    # Long continuous take: continuation only when the renderer can inherit state.
    if exceeds_duration and requirements.continuous_take_required:
        if capability.supports_start_frame:
            mitigations.extend(("export_verified_end_frame", "seed_next_segment_from_verified_frame"))
            return StrategyDecision(
                requirements.transition_id,
                ProductionStrategy.CONTROLLED_CONTINUATION,
                risk,
                tuple(reasons),
                tuple(mitigations),
            )
        if requirements.can_use_cutaways:
            return StrategyDecision(
                requirements.transition_id,
                ProductionStrategy.EDITORIAL_ILLUSION,
                ProductionRisk.HIGH,
                tuple(reasons),
                ("replace_invisible_extension_with_motivated_cutaway",),
            )
        return StrategyDecision(
            requirements.transition_id,
            ProductionStrategy.REDESIGN_REQUIRED,
            ProductionRisk.EXTREME,
            tuple(reasons),
            ("shorten_or_restructure_continuous_take",),
        )

    # Multi-person or high-complexity scenes should be decomposed when possible.
    if exceeds_people or requirements.choreography_complexity >= 3:
        if requirements.can_layer_subjects:
            mitigations.extend(("render_background_plate", "render_subject_groups_separately", "composite_layers"))
            return StrategyDecision(
                requirements.transition_id,
                ProductionStrategy.LAYERED_COMPOSITING,
                risk,
                tuple(reasons),
                tuple(mitigations),
            )
        if requirements.can_use_cutaways:
            return StrategyDecision(
                requirements.transition_id,
                ProductionStrategy.EDITORIAL_ILLUSION,
                risk,
                tuple(reasons),
                ("replace_complex_master_with_coverage_and_cutaways",),
            )
        return StrategyDecision(
            requirements.transition_id,
            ProductionStrategy.REDESIGN_REQUIRED,
            ProductionRisk.EXTREME,
            tuple(reasons),
            ("reduce_character_or_choreography_complexity",),
        )

    # Non-native lip sync is explicitly routed outside direct render.
    if requirements.lip_sync_required and not capability.supports_lip_sync:
        if requirements.external_specialist_available:
            mitigations.append("apply_dedicated_lip_sync_after_visual_acceptance")
            return StrategyDecision(
                requirements.transition_id,
                ProductionStrategy.EXTERNAL_SPECIALIST_STAGE,
                risk,
                tuple(reasons),
                tuple(mitigations),
            )
        return StrategyDecision(
            requirements.transition_id,
            ProductionStrategy.REDESIGN_REQUIRED,
            ProductionRisk.HIGH,
            tuple(reasons),
            ("remove_or_relax_verified_lip_sync_requirement",),
        )

    # Duration can also be solved editorially when continuity is not mandatory.
    if exceeds_duration:
        if requirements.can_use_cutaways:
            return StrategyDecision(
                requirements.transition_id,
                ProductionStrategy.EDITORIAL_ILLUSION,
                risk,
                tuple(reasons),
                ("split_into_music_motivated_shots",),
            )
        return StrategyDecision(
            requirements.transition_id,
            ProductionStrategy.REDESIGN_REQUIRED,
            ProductionRisk.HIGH,
            tuple(reasons),
            ("reduce_duration_to_renderer_limit",),
        )

    return StrategyDecision(
        requirements.transition_id,
        ProductionStrategy.DIRECT_RENDER,
        risk,
        tuple(reasons),
        tuple(mitigations),
    )
