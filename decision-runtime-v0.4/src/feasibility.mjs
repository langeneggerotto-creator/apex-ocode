const ALLOWED_ASSUMPTION_STATUS = new Set(['KNOWN', 'UNKNOWN', 'BLOCKED']);

function requireObject(value, name) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${name} is required before route selection.`);
  }
}

export function validateDecisionContext(context) {
  requireObject(context, 'context');
  if (!String(context.vision ?? '').trim()) {
    throw new Error('A human-visible governing vision is required before route selection.');
  }
  requireObject(context.dreamer, 'context.dreamer');
  requireObject(context.environment, 'context.environment');
  if (!String(context.dreamer.desiredRole ?? '').trim()) {
    throw new Error('The dreamer desired role is required before framework selection.');
  }
  if (!String(context.environment.currentDevice ?? '').trim()) {
    throw new Error('The current device/environment must be identified before framework selection.');
  }
  return true;
}

export function normalizeAssumptions(assumptions = []) {
  return assumptions.map((item) => {
    const status = String(item.status ?? 'UNKNOWN').toUpperCase();
    if (!ALLOWED_ASSUMPTION_STATUS.has(status)) {
      throw new Error(`Unsupported assumption status for ${item.name ?? 'unnamed assumption'}: ${status}`);
    }
    return { name: String(item.name ?? 'unnamed assumption'), status };
  });
}

export function assessCandidateFeasibility(context, candidate) {
  validateDecisionContext(context);
  requireObject(candidate, 'candidate');
  const blockers = [];
  const unknowns = [];
  const warnings = [];

  const supportedDevices = candidate.supportedDevices ?? ['any'];
  const currentDevice = String(context.environment.currentDevice).toLowerCase();
  const deviceFit = supportedDevices.includes('any') || supportedDevices.some((value) => currentDevice.includes(String(value).toLowerCase()));
  if (!deviceFit) blockers.push(`CURRENT_DEVICE_UNSUPPORTED:${context.environment.currentDevice}`);

  for (const dependency of candidate.requiredDependencies ?? []) {
    const status = String(dependency.status ?? 'UNKNOWN').toUpperCase();
    if (status === 'BLOCKED' || status === 'UNAVAILABLE') blockers.push(`DEPENDENCY_${status}:${dependency.name}`);
    else if (status !== 'AVAILABLE' && status !== 'VERIFIED') unknowns.push(`DEPENDENCY_UNKNOWN:${dependency.name}`);
  }

  for (const assumption of normalizeAssumptions(candidate.credentialAssumptions)) {
    if (assumption.status === 'BLOCKED') blockers.push(`CREDENTIAL_BLOCKED:${assumption.name}`);
    if (assumption.status === 'UNKNOWN') unknowns.push(`CREDENTIAL_UNKNOWN:${assumption.name}`);
  }

  const maintenance = candidate.maintenance ?? {};
  if (!String(maintenance.owner ?? '').trim()) unknowns.push('MAINTENANCE_OWNER_UNKNOWN');
  if (!String(maintenance.recovery ?? '').trim()) unknowns.push('RECOVERY_PATH_UNKNOWN');
  if (!String(maintenance.update ?? '').trim()) unknowns.push('UPDATE_PATH_UNKNOWN');
  if (!String(maintenance.operatingCostStatus ?? '').trim()) unknowns.push('OPERATING_COST_UNKNOWN');

  if (candidate.generatedCodeOnly === true) {
    warnings.push('GENERATED_CODE_DOES_NOT_PROVE_DEPLOYMENT_MAINTAINABILITY_OR_FOUNDER_CONTROL');
  }
  if (candidate.localBuildVerified === true && candidate.deploymentVerified !== true) {
    warnings.push('LOCAL_BUILD_DOES_NOT_PROVE_DEPLOYMENT');
  }
  if (candidate.productionValidated !== true) {
    warnings.push('PRODUCTION_VALIDATION_NOT_CLAIMED');
  }
  if (candidate.explicitlyViable === false) blockers.push('CANDIDATE_MARKED_NON_VIABLE');

  const feasibilityStatus = blockers.length > 0 ? 'BLOCKED' : unknowns.length > 0 ? 'NEEDS_EVIDENCE' : 'VIABLE';
  return {
    candidateId: candidate.id,
    feasibilityStatus,
    blockers,
    unknowns,
    warnings,
    reversibleProof: candidate.reversibleProof ?? null,
    maintenance: {
      owner: maintenance.owner ?? 'UNKNOWN',
      recovery: maintenance.recovery ?? 'UNKNOWN',
      update: maintenance.update ?? 'UNKNOWN',
      operatingCostStatus: maintenance.operatingCostStatus ?? 'UNKNOWN'
    }
  };
}

export function assessRouteSet(context, candidates) {
  validateDecisionContext(context);
  if (!Array.isArray(candidates) || candidates.length < 2) {
    throw new Error('At least two plausible routes must be compared before architecture lock.');
  }
  return candidates.map((candidate) => assessCandidateFeasibility(context, candidate));
}
