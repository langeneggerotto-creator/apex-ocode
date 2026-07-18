import { assessRouteSet, validateDecisionContext } from './feasibility.mjs';

const POSITIVE_WEIGHTS = {
  directVisionContribution: 2.0,
  evidenceGain: 1.8,
  successProbability: 1.4,
  userEnvironmentFit: 1.8,
  speedToProof: 1.2,
  reversibility: 1.0,
  ownership: 1.0,
  maintainability: 1.0,
  reuseValue: 0.8
};

const PENALTY_WEIGHTS = {
  costBurden: 0.8,
  complexity: 0.8,
  dependencyBurden: 1.0,
  governanceBurden: 0.6,
  safetyRisk: 1.4,
  lockIn: 1.0
};

function metric(candidate, name, fallback = 0) {
  const value = Number(candidate.metrics?.[name] ?? fallback);
  if (!Number.isFinite(value) || value < 0 || value > 10) {
    throw new Error(`Candidate ${candidate.id} metric ${name} must be between 0 and 10.`);
  }
  return value;
}

function twoConsecutiveEnablingBuilds(history = []) {
  const material = history.filter((item) => item.material !== false).slice(-2);
  return material.length === 2 && material.every((item) => item.kind === 'enabling');
}

export function scoreCandidate(candidate, feasibility, history = []) {
  const disqualifiers = [...feasibility.blockers];
  if (metric(candidate, 'userEnvironmentFit') < 3) disqualifiers.push('USER_ENVIRONMENT_FIT_BELOW_VIABLE_THRESHOLD');
  if (metric(candidate, 'ownership') < 3) disqualifiers.push('OWNERSHIP_BELOW_VIABLE_THRESHOLD');
  if (metric(candidate, 'safetyRisk') >= 9 && candidate.safetyControlsVerified !== true) {
    disqualifiers.push('UNACCEPTABLE_UNCONTROLLED_SAFETY_RISK');
  }
  if (twoConsecutiveEnablingBuilds(history) && candidate.kind !== 'vision-facing' && candidate.safetyException !== true) {
    disqualifiers.push('TWO_BUILD_DETOUR_LIMIT_REQUIRES_VISION_FACING_PROOF');
  }

  let score = 0;
  const contributions = {};
  for (const [name, weight] of Object.entries(POSITIVE_WEIGHTS)) {
    const weighted = metric(candidate, name) * weight;
    contributions[name] = weighted;
    score += weighted;
  }
  for (const [name, weight] of Object.entries(PENALTY_WEIGHTS)) {
    const weighted = metric(candidate, name) * weight;
    contributions[name] = -weighted;
    score -= weighted;
  }
  if (feasibility.feasibilityStatus === 'NEEDS_EVIDENCE') score -= feasibility.unknowns.length * 1.5;
  if (candidate.kind === 'vision-facing') score += 2;

  return {
    candidateId: candidate.id,
    label: candidate.label,
    kind: candidate.kind,
    viable: disqualifiers.length === 0,
    score: Number(score.toFixed(3)),
    disqualifiers,
    feasibilityStatus: feasibility.feasibilityStatus,
    unknowns: feasibility.unknowns,
    warnings: feasibility.warnings,
    contributions
  };
}

export function selectClosestViablePath(context, candidates, options = {}) {
  validateDecisionContext(context);
  const feasibility = assessRouteSet(context, candidates);
  const scored = candidates.map((candidate, index) => scoreCandidate(candidate, feasibility[index], options.history ?? []));
  const ranked = scored
    .filter((item) => item.viable)
    .sort((a, b) => b.score - a.score || a.candidateId.localeCompare(b.candidateId));

  if (ranked.length === 0) {
    return {
      schemaVersion: 'ocode.vision-path-selection-receipt.v0.4',
      decision: 'HOLD_NO_VIABLE_PATH',
      vision: context.vision,
      currentBarrier: context.currentBarrier ?? 'UNKNOWN',
      rankedCandidates: scored.sort((a, b) => b.score - a.score),
      activeRoute: null,
      fallbackRoute: null,
      stopCondition: options.stopCondition ?? null,
      truthStatus: 'NO_VIABLE_PATH__HUMAN_REVIEW_REQUIRED'
    };
  }

  return {
    schemaVersion: 'ocode.vision-path-selection-receipt.v0.4',
    decision: 'PROCEED_WITH_SELECTED_ROUTE',
    vision: context.vision,
    currentBarrier: context.currentBarrier ?? 'UNKNOWN',
    environmentSnapshot: context.environment,
    activeRoute: ranked[0],
    fallbackRoute: ranked[1] ?? null,
    rankedCandidates: [...ranked, ...scored.filter((item) => !item.viable).sort((a, b) => b.score - a.score)],
    stopCondition: options.stopCondition ?? null,
    rerankTriggers: options.rerankTriggers ?? [
      'material evidence changes',
      'environment or device access changes',
      'dependency availability changes',
      'risk, cost, or ownership changes',
      'selected proof succeeds or fails'
    ],
    truthStatus: 'DETERMINISTIC_SELECTION__DECISION_SUPPORT_NOT_AUTONOMOUS_AUTHORITY'
  };
}

export function rerankAfterEvidence(previousReceipt, context, candidates, options = {}) {
  const next = selectClosestViablePath(context, candidates, options);
  return {
    ...next,
    previousActiveRoute: previousReceipt?.activeRoute?.candidateId ?? null,
    routeChanged: (previousReceipt?.activeRoute?.candidateId ?? null) !== (next.activeRoute?.candidateId ?? null)
  };
}
