from dreammusicforge.production_strategy.models import ProductionRisk, ProductionStrategy
from dreammusicforge.providers.kling.models import KlingExecutionPackage, KlingMode
from dreammusicforge.render_verification import MetricResult, RenderCandidate, VerificationDecision, verify_candidate


def package(gates=("technical_validity", "semantic_fidelity", "identity")):
    return KlingExecutionPackage(
        package_id="KLING-T1",
        transition_id="T1",
        strategy=ProductionStrategy.DIRECT_RENDER,
        risk=ProductionRisk.LOW,
        mode=KlingMode.TEXT_TO_VIDEO,
        duration_seconds=5.0,
        prompt="original cinematic music-video asset",
        negative_constraints=("no identity change",),
        references=(),
        candidate_count=2,
        acceptance_gates=gates,
        fallback_plan=(),
        requires_external_master_audio=True,
        requires_external_lip_sync=False,
    )


def candidate(duration=5.0, package_id="KLING-T1"):
    return RenderCandidate("C1", package_id, "c1.mp4", "a" * 64, duration, 1080, 1920, 30.0)


def metric(name, passed=True, critical=True, score=95.0):
    return MetricResult(name, score, passed, critical, f"evidence for {name}")


def test_accepts_when_all_required_gates_pass():
    report = verify_candidate(candidate(), package(), (metric("semantic_fidelity"), metric("identity")))
    assert report.decision is VerificationDecision.ACCEPT


def test_rejects_critical_identity_failure():
    report = verify_candidate(candidate(), package(), (metric("semantic_fidelity"), metric("identity", False)))
    assert report.decision is VerificationDecision.REJECT
    assert "identity" in report.critical_failures


def test_reviews_unresolved_required_gate():
    report = verify_candidate(candidate(), package(), (metric("semantic_fidelity"),))
    assert report.decision is VerificationDecision.REVIEW
    assert "identity" in report.unresolved_gates


def test_rejects_duration_mismatch():
    report = verify_candidate(candidate(duration=6.0), package(), (metric("semantic_fidelity"), metric("identity")))
    assert report.decision is VerificationDecision.REJECT
    assert "duration" in report.critical_failures


def test_rejects_package_mismatch():
    try:
        verify_candidate(candidate(package_id="OTHER"), package(), (metric("semantic_fidelity"), metric("identity")))
    except ValueError as exc:
        assert "package_id" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_noncritical_failure_does_not_block_acceptance():
    report = verify_candidate(candidate(), package(), (metric("semantic_fidelity"), metric("identity"), metric("visual_polish", False, False, 40.0)))
    assert report.decision is VerificationDecision.ACCEPT


def test_negative_tolerance_fails_closed():
    try:
        verify_candidate(candidate(), package(), (metric("semantic_fidelity"), metric("identity")), -0.1)
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_accept_cannot_hide_unresolved_gate():
    report = verify_candidate(candidate(), package(("technical_validity", "semantic_fidelity", "identity", "world")), (metric("semantic_fidelity"), metric("identity")))
    assert report.decision is VerificationDecision.REVIEW
    assert report.unresolved_gates == ("world",)
