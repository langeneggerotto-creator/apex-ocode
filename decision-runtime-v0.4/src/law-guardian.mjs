const TIER_RANK = {
  CONSTITUTIONAL: 4,
  MANDATORY: 3,
  TEMPORARY: 2,
  ADVISORY: 1
};

function normalizedTier(value) {
  const tier = String(value ?? 'ADVISORY').toUpperCase();
  if (!(tier in TIER_RANK)) throw new Error(`Unsupported law tier: ${tier}`);
  return tier;
}

function isApplicable(law, context) {
  const when = law.appliesWhen ?? {};
  if (Array.isArray(when.riskLevels) && !when.riskLevels.includes(context.riskLevel)) return false;
  if (Array.isArray(when.domains) && !when.domains.includes(context.domain)) return false;
  if (Array.isArray(when.tags) && !when.tags.some((tag) => (context.tags ?? []).includes(tag))) return false;
  return law.status !== 'SUSPENDED' && law.status !== 'RETIRED';
}

function validateLaw(law) {
  const tier = normalizedTier(law.tier);
  const errors = [];
  if (!law.id) errors.push('LAW_ID_REQUIRED');
  if (!law.controlKey) errors.push('CONTROL_KEY_REQUIRED');
  if ((tier === 'CONSTITUTIONAL' || tier === 'MANDATORY') && !String(law.failureMode ?? '').trim()) {
    errors.push('BINDING_RULE_REQUIRES_NAMED_FAILURE_MODE');
  }
  if (tier === 'TEMPORARY' && !law.expiresAt && !law.reviewAt) {
    errors.push('TEMPORARY_RULE_REQUIRES_EXPIRY_OR_REVIEW');
  }
  return { tier, errors };
}

export function compileActiveLawSet(laws, context, options = {}) {
  if (!Array.isArray(laws)) throw new Error('laws must be an array');
  const rejected = [];
  const applicable = [];

  for (const law of laws) {
    const validation = validateLaw(law);
    if (validation.errors.length > 0) {
      rejected.push({ lawId: law.id ?? 'UNKNOWN', errors: validation.errors });
      continue;
    }
    const normalized = { ...law, tier: validation.tier };
    if (isApplicable(normalized, context)) applicable.push(normalized);
  }

  const grouped = new Map();
  for (const law of applicable) {
    const current = grouped.get(law.controlKey) ?? [];
    current.push(law);
    grouped.set(law.controlKey, current);
  }

  const activeControls = [];
  const simplificationRecommendations = [];
  for (const [controlKey, group] of grouped.entries()) {
    const ordered = [...group].sort((a, b) => TIER_RANK[b.tier] - TIER_RANK[a.tier] || String(a.id).localeCompare(String(b.id)));
    const primary = ordered[0];
    const strictestTier = primary.tier;
    if (group.length > 1) {
      simplificationRecommendations.push({
        action: 'MERGE_DUPLICATES_INTO_ONE_VISIBLE_CONTROL',
        controlKey,
        sourceLawIds: ordered.map((law) => law.id),
        preservedTier: strictestTier
      });
    }
    activeControls.push({
      controlKey,
      title: primary.title,
      tier: strictestTier,
      action: primary.action,
      failureMode: primary.failureMode ?? null,
      sourceLawIds: ordered.map((law) => law.id),
      evidenceRequired: [...new Set(ordered.flatMap((law) => law.evidenceRequired ?? []))],
      approvalRequired: ordered.some((law) => law.approvalRequired === true),
      reviewAt: ordered.map((law) => law.reviewAt).filter(Boolean).sort()[0] ?? null,
      expiresAt: ordered.map((law) => law.expiresAt).filter(Boolean).sort()[0] ?? null
    });
  }

  const conflicts = [];
  const conflictGroups = new Map();
  for (const law of applicable.filter((law) => law.conflictGroup && law.requiredOutcome)) {
    const group = conflictGroups.get(law.conflictGroup) ?? [];
    group.push(law);
    conflictGroups.set(law.conflictGroup, group);
  }
  for (const [conflictGroup, group] of conflictGroups.entries()) {
    const outcomes = [...new Set(group.map((law) => law.requiredOutcome))];
    if (outcomes.length > 1) {
      conflicts.push({
        conflictGroup,
        outcomes,
        sourceLawIds: group.map((law) => law.id),
        resolution: 'HUMAN_DECISION_REQUIRED'
      });
    }
  }

  if (Array.isArray(options.requestedDowngrades)) {
    for (const request of options.requestedDowngrades) {
      const control = activeControls.find((item) => item.controlKey === request.controlKey);
      if (control && (control.tier === 'CONSTITUTIONAL' || control.tier === 'MANDATORY')) {
        rejected.push({
          lawId: control.sourceLawIds.join(','),
          errors: ['MANDATORY_CONTROL_CANNOT_BE_DOWNGRADED_MERELY_TO_REDUCE_BURDEN']
        });
      }
    }
  }

  const burdenUnits = activeControls.reduce((sum, control) => {
    return sum + 1 + control.evidenceRequired.length + (control.approvalRequired ? 2 : 0);
  }, 0);
  const protectionUnits = activeControls.reduce((sum, control) => {
    return sum + TIER_RANK[control.tier] + (control.failureMode ? 1 : 0);
  }, 0);

  return {
    schemaVersion: 'ocode.active-law-receipt.v0.4',
    decision: conflicts.length > 0 ? 'HOLD_FOR_HUMAN_CONFLICT_RESOLUTION' : 'PROCEED_WITH_ACTIVE_CONTROLS',
    context: {
      domain: context.domain ?? 'general',
      riskLevel: context.riskLevel ?? 'unknown',
      tags: context.tags ?? []
    },
    activeControls: activeControls.sort((a, b) => TIER_RANK[b.tier] - TIER_RANK[a.tier] || a.controlKey.localeCompare(b.controlKey)),
    conflicts,
    rejected,
    simplificationRecommendations,
    metrics: {
      sourceLawCount: laws.length,
      applicableLawCount: applicable.length,
      visibleControlCount: activeControls.length,
      burdenUnits,
      protectionUnits
    },
    truthStatus: 'COMPILED_POLICY_RECEIPT__RUNTIME_DECISION_SUPPORT__NOT_LEGAL_AUTHORITY'
  };
}
