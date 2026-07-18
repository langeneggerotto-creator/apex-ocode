import crypto from 'node:crypto';

function compact(values) {
  return [...new Set(values.filter(Boolean))];
}

function recordId(receipt, provenance) {
  const seed = `${receipt.task.taskId}|${receipt.generatedAt}|${provenance.registry_sha256}|${receipt.decision}`;
  return `CORE-OS-POLICY-${crypto.createHash('sha256').update(seed).digest('hex').slice(0, 20)}`;
}

function blockerText(blocker) {
  if (blocker.code === 'MISSING_REQUIRED_EVIDENCE') return `${blocker.code}:${(blocker.missing ?? []).join(',')}`;
  return blocker.code ?? JSON.stringify(blocker);
}

export function buildCoreOsPolicyEvidenceRecord({ receipt, bundle, subject = {}, producer = {}, review = {} }) {
  const unresolvedGaps = compact([
    ...(receipt.blockers ?? []).map(blockerText),
    ...(receipt.advisoryWarnings ?? []).map((warning) => warning.code),
    bundle.provenance.drift_check_required ? 'CANONICAL_REGISTRY_DRIFT_CHECK_REQUIRED' : null
  ]);
  const humanRequired = receipt.decision === 'HOLD_FOR_HUMAN_REVIEW' || (receipt.conflicts ?? []).some((item) => item.material);

  return {
    record_id: recordId(receipt, bundle.provenance),
    record_type: 'CORE_OS_POLICY_EVIDENCE',
    schema_version: '0.1',
    created_at: new Date().toISOString(),
    producer: {
      repository: producer.repository ?? 'langeneggerotto-creator/apex-ocode',
      module: producer.module ?? 'OCODE Law Guardian and Policy Compiler',
      version: producer.version ?? '0.2.0',
      commit: producer.commit ?? null
    },
    subject: {
      repository: subject.repository ?? 'UNSPECIFIED',
      project: subject.project ?? 'UNSPECIFIED',
      module: subject.module ?? 'UNSPECIFIED',
      artifact: subject.artifact ?? receipt.task.taskId,
      version: subject.version ?? 'UNSPECIFIED'
    },
    inherited_law: bundle.provenance,
    applicable_readiness_dimensions: bundle.dimensions,
    implementation_status: review.implementationStatus ?? 'PARTIALLY_IMPLEMENTED',
    policy_decision: receipt.decision,
    current_weakest_barrier: receipt.blockers?.[0]?.code ?? null,
    selected_gap_response: review.selectedGapResponse ?? (receipt.decision === 'HOLD_FOR_HUMAN_REVIEW' ? 'DEFER' : null),
    alternatives_route_fit: review.alternativesRouteFit ?? [],
    ownership_portability_maintenance_recovery: review.ownershipReview ?? {
      status: 'UNKNOWN',
      note: 'Not assessed by the policy compiler unless supplied by the calling workflow.'
    },
    anti_paralysis_result: review.antiParalysisResult ?? {
      status: 'CONSTRAINED',
      movement_artifact: `Policy receipt ${receipt.task.taskId}`,
      next_action: 'Execute or review the compiled controls and record outcome evidence.'
    },
    evidence_references: compact([
      `sha256:registry:${bundle.provenance.registry_sha256}`,
      `sha256:contract:${bundle.provenance.contract_sha256}`,
      `sha256:policy-map:${bundle.provenance.policy_map_sha256}`,
      ...(review.evidenceReferences ?? [])
    ]),
    unresolved_gaps: unresolvedGaps,
    exceptions: review.exceptions ?? [],
    human_approval: {
      required: humanRequired,
      status: humanRequired ? 'PENDING' : 'NOT_REQUIRED',
      approver: null,
      approved_at: null,
      ...(review.humanApproval ?? {})
    },
    promotion_decision: review.promotionDecision ?? (receipt.decision === 'HOLD_FOR_HUMAN_REVIEW' ? 'HOLD' : 'NOT_APPLICABLE'),
    reassessment_trigger: review.reassessmentTrigger ?? 'Reassess before material commitment, architecture lock, external action, deployment, scaling, delegation, handoff, or after new evidence.',
    policy_receipt: receipt,
    truth_boundary: 'This record proves that OCODE loaded a provenance-recorded Core OS registry bundle, compiled an active law set, and produced a schema-valid evidence record. It does not prove that runtime controls were executed, the canonical private repository has not changed since a pinned snapshot, or the subject is operationally compliant.'
  };
}
