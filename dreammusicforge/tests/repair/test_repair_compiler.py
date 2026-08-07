from dreammusicforge.repair import RepairAction, compile_repair_contract
from dreammusicforge.render_verification.models import MetricResult, VerificationDecision, VerificationReport


def report(*, decision=VerificationDecision.REJECT, failures=(), unresolved=(), metrics=()):
    return VerificationReport(
        candidate_id="CAND-001",
        package_id="KLING-T001",
        decision=decision,
        metrics=tuple(metrics) or (
            MetricResult("identity", 98.0, True, True, "reference comparison"),
            MetricResult("costume", 99.0, True, True, "topology comparison"),
            MetricResult("world", 97.0, True, True, "set comparison"),
            MetricResult("lip_sync", 55.0, False, True, "timing mismatch"),
        ),
        critical_failures=tuple(failures),
        unresolved_gates=tuple(unresolved),
        reasons=("test",),
    )


def test_lip_sync_routes_to_specialist_and_preserves_picture():
    contract = compile_repair_contract(report(failures=("lip_sync",)))
    assert contract.action is RepairAction.RELIP_SYNC
    assert set(contract.preserve_metrics) == {"identity", "costume", "world"}
    assert contract.change_metrics == ("lip_sync",)


def test_identity_failure_regenerates():
    metrics = (
        MetricResult("identity", 50.0, False, True, "drift"),
        MetricResult("costume", 99.0, True, True, "pass"),
    )
    contract = compile_repair_contract(report(failures=("identity",), metrics=metrics))
    assert contract.action is RepairAction.REGENERATE
    assert contract.preserve_metrics == ("costume",)


def test_continuity_failure_uses_editorial_concealment():
    metrics = (
        MetricResult("state_continuity", 45.0, False, True, "seam jump"),
        MetricResult("identity", 98.0, True, True, "pass"),
    )
    contract = compile_repair_contract(report(failures=("state_continuity",), metrics=metrics))
    assert contract.action is RepairAction.EDITORIAL_CONCEALMENT


def test_duration_failure_shortens_shot():
    metrics = (MetricResult("duration", 40.0, False, True, "too long"),)
    contract = compile_repair_contract(report(failures=("duration",), metrics=metrics))
    assert contract.action is RepairAction.SHORTEN_SHOT


def test_unresolved_only_routes_to_manual_review():
    metrics = (MetricResult("identity", 98.0, True, True, "pass"),)
    contract = compile_repair_contract(report(decision=VerificationDecision.REVIEW, unresolved=("lip_sync",), metrics=metrics))
    assert contract.action is RepairAction.MANUAL_REVIEW
    assert contract.change_metrics == ("lip_sync",)


def test_accepted_candidate_cannot_be_repaired():
    metrics = (MetricResult("identity", 98.0, True, True, "pass"),)
    try:
        compile_repair_contract(report(decision=VerificationDecision.ACCEPT, metrics=metrics))
    except ValueError as exc:
        assert "do not require repair" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_unknown_failure_redesigns_task():
    metrics = (MetricResult("semantic_fidelity", 20.0, False, True, "wrong event"),)
    contract = compile_repair_contract(report(failures=("semantic_fidelity",), metrics=metrics))
    assert contract.action is RepairAction.REDESIGN_TASK


def test_preserve_and_change_sets_never_overlap():
    contract = compile_repair_contract(report(failures=("lip_sync",)))
    assert not (set(contract.preserve_metrics) & set(contract.change_metrics))
