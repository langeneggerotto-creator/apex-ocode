from __future__ import annotations

from dreammusicforge.render_verification.models import VerificationDecision, VerificationReport
from .models import RepairAction, RepairContract


def _choose_action(report: VerificationReport) -> RepairAction:
    failed = set(report.critical_failures)
    unresolved = set(report.unresolved_gates)

    if report.decision is VerificationDecision.ACCEPT:
        raise ValueError("accepted candidates do not require repair")
    if unresolved and not failed:
        return RepairAction.MANUAL_REVIEW
    if "lip_sync" in failed:
        return RepairAction.RELIP_SYNC
    if failed & {"identity", "costume", "world"}:
        return RepairAction.REGENERATE
    if failed & {"state_continuity", "causal_continuity"}:
        return RepairAction.EDITORIAL_CONCEALMENT
    if failed & {"duration", "technical_validity"}:
        return RepairAction.SHORTEN_SHOT
    if failed & {"layer", "composite"}:
        return RepairAction.REPLACE_LAYER
    if failed:
        return RepairAction.REDESIGN_TASK
    return RepairAction.MANUAL_REVIEW


def compile_repair_contract(report: VerificationReport) -> RepairContract:
    report.validate()
    action = _choose_action(report)

    failed = set(report.critical_failures)
    unresolved = set(report.unresolved_gates)
    all_metrics = {metric.name for metric in report.metrics}
    passing = {
        metric.name
        for metric in report.metrics
        if metric.passed is True and metric.name not in failed
    }

    change_metrics = tuple(sorted(failed or unresolved))
    preserve_metrics = tuple(sorted(passing - set(change_metrics)))

    instructions: list[str] = [
        "Preserve every passing canonical dimension exactly unless this repair contract explicitly authorizes a change.",
        "Do not allow renderer output to redefine Film Genome, Experience Graph, Production Twin, or accepted continuity state.",
    ]

    if action is RepairAction.REGENERATE:
        instructions.append("Regenerate the candidate with stronger references and constraints only for the failed dimensions.")
    elif action is RepairAction.RELIP_SYNC:
        instructions.append("Preserve accepted picture state and route the locked vocal interval through the dedicated lip-sync stage.")
    elif action is RepairAction.REPLACE_LAYER:
        instructions.append("Replace only the failed production layer and keep all accepted layers immutable.")
    elif action is RepairAction.SHORTEN_SHOT:
        instructions.append("Trim or re-segment the shot to remove the invalid duration/technical region without changing accepted creative state.")
    elif action is RepairAction.EDITORIAL_CONCEALMENT:
        instructions.append("Use the least invasive editorial bridge, cutaway, wipe, or shortened boundary that restores causal continuity.")
    elif action is RepairAction.REDESIGN_TASK:
        instructions.append("Return the task to Production Strategy for a safer executable design because direct repair is not sufficiently bounded.")
    else:
        instructions.append("Do not mutate the candidate automatically; obtain missing evidence or human review for unresolved gates.")

    contract = RepairContract(
        repair_id=f"REPAIR-{report.candidate_id}",
        candidate_id=report.candidate_id,
        package_id=report.package_id,
        action=action,
        preserve_metrics=preserve_metrics,
        change_metrics=change_metrics,
        instructions=tuple(instructions),
        critical_failures=tuple(sorted(failed)),
        unresolved_gates=tuple(sorted(unresolved)),
    )
    contract.validate()

    if set(contract.preserve_metrics) | set(contract.change_metrics) - all_metrics:
        # The report may name a required gate not present as a measured metric; that is
        # allowed only as unresolved evidence and remains fail-closed.
        unknown_changes = set(contract.change_metrics) - all_metrics
        if unknown_changes - unresolved:
            raise ValueError("repair references unknown non-unresolved metrics")

    return contract
