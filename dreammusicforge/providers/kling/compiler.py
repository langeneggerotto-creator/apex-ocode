from __future__ import annotations

from dataclasses import dataclass

from dreammusicforge.production_strategy.models import (
    CapabilityProfile,
    ProductionStrategy,
    StrategyDecision,
    TransitionRequirements,
)
from .models import KlingExecutionPackage, KlingMode, KlingReference


@dataclass(frozen=True)
class KlingCreativeContract:
    performer_id: str
    costume_id: str
    world_id: str
    action: str
    camera: str
    lighting: str
    emotion: str
    song_interval: str
    start_frame_id: str | None = None
    character_reference_id: str | None = None
    world_reference_id: str | None = None
    costume_reference_id: str | None = None
    motion_reference_id: str | None = None

    def validate(self) -> None:
        for name, value in (
            ("performer_id", self.performer_id),
            ("costume_id", self.costume_id),
            ("world_id", self.world_id),
            ("action", self.action),
            ("camera", self.camera),
            ("lighting", self.lighting),
            ("emotion", self.emotion),
            ("song_interval", self.song_interval),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")


def _mode_for(strategy: ProductionStrategy, contract: KlingCreativeContract) -> KlingMode:
    if strategy is ProductionStrategy.DIRECT_RENDER:
        return KlingMode.IMAGE_TO_VIDEO if contract.start_frame_id else KlingMode.TEXT_TO_VIDEO
    if strategy is ProductionStrategy.CONTROLLED_CONTINUATION:
        return KlingMode.START_FRAME_CONTINUATION
    if strategy is ProductionStrategy.LAYERED_COMPOSITING:
        return KlingMode.LAYERED_PASS
    if strategy is ProductionStrategy.EDITORIAL_ILLUSION:
        return KlingMode.MULTI_SHOT
    if strategy is ProductionStrategy.EXTERNAL_SPECIALIST_STAGE:
        return KlingMode.EXTERNAL_STAGE
    return KlingMode.REDESIGN


def _references(contract: KlingCreativeContract, strategy: ProductionStrategy) -> tuple[KlingReference, ...]:
    refs: list[KlingReference] = []
    if contract.character_reference_id:
        refs.append(KlingReference(contract.character_reference_id, "CHARACTER", True, "preserve performer identity"))
    if contract.costume_reference_id:
        refs.append(KlingReference(contract.costume_reference_id, "COSTUME", True, "preserve garment topology"))
    if contract.world_reference_id:
        refs.append(KlingReference(contract.world_reference_id, "WORLD", True, "preserve set geometry and visual world"))
    if contract.start_frame_id:
        refs.append(KlingReference(contract.start_frame_id, "START_FRAME", strategy is ProductionStrategy.CONTROLLED_CONTINUATION, "inherit verified source state"))
    if contract.motion_reference_id:
        refs.append(KlingReference(contract.motion_reference_id, "MOTION", False, "guide planned performance movement"))
    return tuple(refs)


def _prompt(contract: KlingCreativeContract, requirements: TransitionRequirements, strategy: ProductionStrategy) -> str:
    if strategy in {ProductionStrategy.EXTERNAL_SPECIALIST_STAGE, ProductionStrategy.REDESIGN_REQUIRED}:
        return ""
    continuity = "Preserve performer identity, costume topology, world geometry, lighting family, and causal motion unless explicitly changed by this contract."
    if strategy is ProductionStrategy.CONTROLLED_CONTINUATION:
        continuity += " Begin from the verified source frame and continue time naturally; do not restart the performance or camera move."
    if strategy is ProductionStrategy.LAYERED_COMPOSITING:
        continuity += " Render only the assigned production layer; do not invent missing ensemble or composite elements."
    if strategy is ProductionStrategy.EDITORIAL_ILLUSION:
        continuity += " Favor a clean editorially useful shot that preserves the intended experience rather than literal impossible complexity."
    return (
        f"Create an original cinematic music-video production asset for {contract.song_interval}. "
        f"Performer: {contract.performer_id}. Costume: {contract.costume_id}. World: {contract.world_id}. "
        f"Primary action: {contract.action}. Camera: {contract.camera}. Lighting: {contract.lighting}. "
        f"Intended emotional state: {contract.emotion}. Character count: {requirements.character_count}. "
        f"{continuity} Music is governed by the external canonical master song; do not invent or restart the final soundtrack."
    )


def _negative_constraints(requirements: TransitionRequirements) -> tuple[str, ...]:
    constraints = [
        "no unintended identity change",
        "no unintended hairstyle change",
        "no unintended costume redesign",
        "no unintended world redesign",
        "no arbitrary camera reset",
        "no final-song replacement",
    ]
    if requirements.exact_world_required:
        constraints.append("no set-geometry mutation")
    if requirements.exact_costume_required:
        constraints.append("no garment-topology mutation")
    if requirements.continuous_take_required:
        constraints.append("no unexplained temporal reset")
    return tuple(constraints)


def _acceptance_gates(requirements: TransitionRequirements) -> tuple[str, ...]:
    gates = ["technical_validity", "semantic_fidelity"]
    if requirements.exact_identity_required:
        gates.append("identity")
    if requirements.exact_costume_required:
        gates.append("costume")
    if requirements.exact_world_required:
        gates.append("world")
    if requirements.lip_sync_required:
        gates.append("lip_sync")
    if requirements.continuous_take_required:
        gates.extend(("state_continuity", "causal_continuity"))
    return tuple(gates)


def compile_kling_package(
    decision: StrategyDecision,
    requirements: TransitionRequirements,
    capability: CapabilityProfile,
    contract: KlingCreativeContract,
) -> KlingExecutionPackage:
    requirements.validate()
    capability.validate()
    contract.validate()
    if decision.transition_id != requirements.transition_id:
        raise ValueError("strategy decision does not match transition requirements")
    if capability.renderer_id.lower().find("kling") < 0:
        raise ValueError("Kling compiler requires a Kling capability profile")

    mode = _mode_for(decision.strategy, contract)
    if decision.strategy is ProductionStrategy.CONTROLLED_CONTINUATION:
        if not capability.supports_start_frame or not contract.start_frame_id:
            raise ValueError("controlled continuation requires Kling start-frame support and a verified start frame")
    if requirements.exact_identity_required and not capability.supports_character_reference and not contract.character_reference_id:
        raise ValueError("exact identity requires character-reference capability or an explicit character reference")
    if requirements.duration_seconds > capability.max_duration_seconds and decision.strategy is ProductionStrategy.DIRECT_RENDER:
        raise ValueError("direct render exceeds renderer maximum duration")

    package = KlingExecutionPackage(
        package_id=f"KLING-{requirements.transition_id}",
        transition_id=requirements.transition_id,
        strategy=decision.strategy,
        risk=decision.risk,
        mode=mode,
        duration_seconds=min(requirements.duration_seconds, capability.max_duration_seconds)
        if decision.strategy is ProductionStrategy.CONTROLLED_CONTINUATION
        else requirements.duration_seconds,
        prompt=_prompt(contract, requirements, decision.strategy),
        negative_constraints=_negative_constraints(requirements),
        references=_references(contract, decision.strategy),
        candidate_count=4 if decision.risk.value in {"HIGH", "EXTREME"} else 2,
        acceptance_gates=_acceptance_gates(requirements),
        fallback_plan=decision.mitigations,
        requires_external_master_audio=True,
        requires_external_lip_sync=requirements.lip_sync_required and not capability.supports_lip_sync,
    )
    package.validate()
    return package
