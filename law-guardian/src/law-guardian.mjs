const VALID_TIERS = new Set([0, 1, 2, 3, 4, 5]);
const VALID_MODES = new Set([
  'EXPLORATION', 'PROTOTYPE', 'BUILD', 'PILOT', 'PRODUCTION', 'HIGH_STAKES'
]);
const VALID_RISKS = new Set(['LOW', 'MODERATE', 'HIGH', 'CRITICAL', 'UNKNOWN']);
const RISK_ORDER = Object.freeze({ LOW: 1, MODERATE: 2, HIGH: 3, CRITICAL: 4, UNKNOWN: 4 });
const TIER_NAMES = Object.freeze({
  0: 'CONSTITUTIONAL',
  1: 'UNIVERSAL_OPERATING',
  2: 'DOMAIN',
  3: 'PROJECT',
  4: 'TEMPORARY',
  5: 'ADVISORY'
});

export class LawGuardianError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = 'LawGuardianError';
    this.details = details;
  }
}

function asArray(value) {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}

function unique(values) {
  return [...new Set(values.filter((value) => value != null && value !== ''))];
}

function normalizeEnum(value, valid, fallback) {
  const normalized = String(value ?? '').trim().toUpperCase();
  return valid.has(normalized) ? normalized : fallback;
}

function dateState(law, now) {
  const reviewDate = law.reviewDate ? new Date(law.reviewDate) : null;
  const expiryDate = law.expiryDate ? new Date(law.expiryDate) : null;
  return {
    reviewDue: Boolean(reviewDate && !Number.isNaN(reviewDate.valueOf()) && reviewDate <= now),
    expired: Boolean(expiryDate && !Number.isNaN(expiryDate.valueOf()) && expiryDate < now)
  };
}

export function classifyContext(input = {}) {
  const mode = normalizeEnum(input.mode, VALID_MODES, 'EXPLORATION');
  const riskLevel = normalizeEnum(input.riskLevel, VALID_RISKS, 'UNKNOWN');
  const domain = String(input.domain ?? 'GENERAL').trim().toUpperCase() || 'GENERAL';
  const tags = unique(asArray(input.tags).map((tag) => String(tag).trim().toUpperCase()));
  const authorityLevel = String(input.authorityLevel ?? 'RECOMMENDATION_ONLY').trim().toUpperCase();
  const reversible = input.reversible !== false;
  const affectedParties = Math.max(1, Number(input.affectedParties ?? 1) || 1);
  const commitments = {
    money: Math.max(0, Number(input.commitments?.money ?? 0) || 0),
    timeHours: Math.max(0, Number(input.commitments?.timeHours ?? 0) || 0),
    externalWrites: Math.max(0, Number(input.commitments?.externalWrites ?? 0) || 0),
    reputation: Math.max(0, Math.min(5, Number(input.commitments?.reputation ?? 0) || 0))
  };

  let riskScore = RISK_ORDER[riskLevel];
  if (!reversible) riskScore += 1;
  if (affectedParties > 10) riskScore += 1;
  if (affectedParties > 100) riskScore += 1;
  if (commitments.money >= 1_000) riskScore += 1;
  if (commitments.money >= 10_000) riskScore += 1;
  if (commitments.externalWrites > 0) riskScore += 1;
  if (commitments.reputation >= 3) riskScore += 1;
  if (mode === 'PRODUCTION' || mode === 'HIGH_STAKES') riskScore += 1;
  riskScore = Math.min(8, riskScore);

  return {
    taskId: String(input.taskId ?? 'UNSPECIFIED_TASK'),
    description: String(input.description ?? ''),
    domain,
    mode,
    riskLevel,
    riskScore,
    authorityLevel,
    reversible,
    affectedParties,
    commitments,
    tags,
    evidence: { ...(input.evidence ?? {}) },
    requestedExceptions: asArray(input.requestedExceptions),
    classifiedAt: new Date().toISOString()
  };
}

export function normalizeLaw(rawLaw, now = new Date()) {
  if (!rawLaw || typeof rawLaw !== 'object') {
    throw new LawGuardianError('Law must be an object.');
  }
  const id = String(rawLaw.id ?? '').trim();
  if (!id) throw new LawGuardianError('Law id is required.', { rawLaw });

  const requestedTier = Number(rawLaw.tier);
  let tier = VALID_TIERS.has(requestedTier) ? requestedTier : 5;
  const warnings = [];
  const mandatory = Boolean(rawLaw.mandatory || rawLaw.constitutional || tier === 0);
  const failureMode = String(rawLaw.failureMode ?? '').trim();

  if (tier < 5 && !failureMode) {
    if (tier === 0 || mandatory) {
      warnings.push('BINDING_LAW_MISSING_FAILURE_MODE_REPAIR_REQUIRED');
    } else {
      tier = 5;
      warnings.push('DOWNGRADED_TO_ADVISORY_NO_FAILURE_MODE');
    }
  }

  const state = dateState(rawLaw, now);
  if (state.expired) warnings.push('EXPIRED_RULE');
  if (state.reviewDue) warnings.push('REVIEW_DUE');

  return {
    id,
    title: String(rawLaw.title ?? id),
    tier,
    tierName: TIER_NAMES[tier],
    status: String(rawLaw.status ?? 'CANDIDATE').toUpperCase(),
    mandatory,
    constitutional: Boolean(rawLaw.constitutional || tier === 0),
    domains: unique(asArray(rawLaw.domains ?? '*').map((value) => String(value).toUpperCase())),
    modes: unique(asArray(rawLaw.modes ?? '*').map((value) => String(value).toUpperCase())),
    riskLevels: unique(asArray(rawLaw.riskLevels ?? '*').map((value) => String(value).toUpperCase())),
    triggers: unique(asArray(rawLaw.triggers).map((value) => String(value).toUpperCase())),
    failureMode,
    protectedValue: String(rawLaw.protectedValue ?? '').trim(),
    controls: unique(asArray(rawLaw.controls).map(String)),
    requiredEvidence: unique(asArray(rawLaw.requiredEvidence).map(String)),
    mergeKey: String(rawLaw.mergeKey ?? id),
    conflictsWith: unique(asArray(rawLaw.conflictsWith).map(String)),
    burden: Math.max(0, Math.min(10, Number(rawLaw.burden ?? 1) || 0)),
    protection: Math.max(0, Math.min(10, Number(rawLaw.protection ?? 1) || 0)),
    reviewDate: rawLaw.reviewDate ?? null,
    expiryDate: rawLaw.expiryDate ?? null,
    source: String(rawLaw.source ?? 'UNSPECIFIED'),
    rationale: String(rawLaw.rationale ?? ''),
    warnings,
    expired: state.expired,
    reviewDue: state.reviewDue
  };
}

function matchesDimension(configuredValues, actual) {
  return configuredValues.includes('*') || configuredValues.includes(actual);
}

function triggerMatches(law, context) {
  if (law.triggers.length === 0) return true;
  return law.triggers.some((trigger) => context.tags.includes(trigger));
}

export function evaluateApplicability(law, context) {
  const reasons = [];
  const exclusions = [];

  if (law.expired) exclusions.push('EXPIRED');
  if (!matchesDimension(law.domains, context.domain)) exclusions.push('DOMAIN_NOT_APPLICABLE');
  if (!matchesDimension(law.modes, context.mode)) exclusions.push('MODE_NOT_APPLICABLE');
  if (!matchesDimension(law.riskLevels, context.riskLevel)) exclusions.push('RISK_NOT_APPLICABLE');
  if (!triggerMatches(law, context)) exclusions.push('TRIGGER_NOT_PRESENT');

  if (law.constitutional && exclusions.length === 0) reasons.push('CONSTITUTIONAL_PROTECTION');
  if (law.mandatory && exclusions.length === 0) reasons.push('MANDATORY_WHEN_APPLICABLE');
  if (law.tier === 5 && exclusions.length === 0) reasons.push('ADVISORY_ONLY');

  return {
    applicable: exclusions.length === 0,
    reasons,
    exclusions
  };
}

function mergeLawGroup(group) {
  const sorted = [...group].sort((a, b) => a.tier - b.tier || b.protection - a.protection);
  const primary = sorted[0];
  return {
    id: `COMPILED:${primary.mergeKey}`,
    mergeKey: primary.mergeKey,
    title: primary.title,
    tier: Math.min(...group.map((law) => law.tier)),
    tierName: TIER_NAMES[Math.min(...group.map((law) => law.tier))],
    mandatory: group.some((law) => law.mandatory),
    constitutional: group.some((law) => law.constitutional),
    failureModes: unique(group.map((law) => law.failureMode)),
    protectedValues: unique(group.map((law) => law.protectedValue)),
    controls: unique(group.flatMap((law) => law.controls)),
    requiredEvidence: unique(group.flatMap((law) => law.requiredEvidence)),
    sourceLawIds: group.map((law) => law.id),
    sources: unique(group.map((law) => law.source)),
    conflictsWith: unique(group.flatMap((law) => law.conflictsWith)),
    burden: Math.max(...group.map((law) => law.burden)),
    protection: Math.max(...group.map((law) => law.protection)),
    warnings: unique(group.flatMap((law) => law.warnings)),
    reviewDue: group.some((law) => law.reviewDue)
  };
}

export function mergeDuplicateLaws(applicableLaws) {
  const groups = new Map();
  for (const law of applicableLaws) {
    const key = law.mergeKey || law.id;
    const current = groups.get(key) ?? [];
    current.push(law);
    groups.set(key, current);
  }
  return [...groups.values()].map(mergeLawGroup);
}

export function detectConflicts(compiledLaws) {
  const activeIds = new Set(compiledLaws.flatMap((law) => law.sourceLawIds));
  const conflicts = [];
  for (const law of compiledLaws) {
    for (const conflictId of law.conflictsWith) {
      if (activeIds.has(conflictId)) {
        const pair = [law.sourceLawIds[0], conflictId].sort();
        const key = pair.join('::');
        if (!conflicts.some((item) => item.key === key)) {
          conflicts.push({
            key,
            laws: pair,
            material: law.mandatory || law.constitutional || law.tier <= 2,
            resolution: 'HUMAN_REVIEW_REQUIRED'
          });
        }
      }
    }
  }
  return conflicts;
}

function evaluateEvidence(compiledLaw, context) {
  const missing = compiledLaw.requiredEvidence.filter((key) => context.evidence[key] !== true);
  return {
    missing,
    satisfied: missing.length === 0
  };
}

function governanceMetrics(compiledLaws) {
  const burden = compiledLaws.reduce((sum, law) => sum + law.burden, 0);
  const protection = compiledLaws.reduce((sum, law) => sum + law.protection, 0);
  const efficiency = burden === 0 ? protection : Number((protection / burden).toFixed(2));
  return { burden, protection, efficiency };
}

function buildSimplificationRecommendations(compiledLaws, metrics) {
  const recommendations = [];
  if (metrics.burden > metrics.protection * 1.25) {
    recommendations.push({
      action: 'SIMPLIFY_ACTIVE_SET',
      reason: 'GOVERNANCE_BURDEN_EXCEEDS_ESTIMATED_PROTECTION',
      protectedConstraints: 'Do not remove constitutional, mandatory, legal, safety, consent, ownership, or truth controls.'
    });
  }
  for (const law of compiledLaws) {
    if (law.sourceLawIds.length > 1) {
      recommendations.push({
        action: 'MERGED_DUPLICATE_CONTROLS',
        mergeKey: law.mergeKey,
        sourceLawIds: law.sourceLawIds,
        userFacingControlCount: law.controls.length
      });
    }
    if (law.reviewDue) {
      recommendations.push({ action: 'REVIEW_DUE', sourceLawIds: law.sourceLawIds });
    }
  }
  return recommendations;
}

export function compilePolicy(rawLaws, rawContext, options = {}) {
  const now = options.now ? new Date(options.now) : new Date();
  if (Number.isNaN(now.valueOf())) throw new LawGuardianError('Invalid now date.');

  const context = classifyContext(rawContext);
  const normalizedLaws = rawLaws.map((law) => normalizeLaw(law, now));
  const applicable = [];
  const consideredButInactive = [];

  for (const law of normalizedLaws) {
    const evaluation = evaluateApplicability(law, context);
    if (evaluation.applicable) {
      applicable.push(law);
    } else {
      consideredButInactive.push({ id: law.id, title: law.title, reasons: evaluation.exclusions });
    }
  }

  const compiledLaws = mergeDuplicateLaws(applicable);
  const conflicts = detectConflicts(compiledLaws);
  const blockers = [];
  const advisoryWarnings = [];

  if (context.riskLevel === 'UNKNOWN') {
    blockers.push({ code: 'UNKNOWN_RISK_NOT_READY', message: 'Risk level is unknown and cannot be treated as ready.' });
  }

  for (const law of compiledLaws) {
    const evidence = evaluateEvidence(law, context);
    law.evidenceStatus = evidence;
    if (!evidence.satisfied) {
      const record = {
        code: 'MISSING_REQUIRED_EVIDENCE',
        lawId: law.id,
        sourceLawIds: law.sourceLawIds,
        missing: evidence.missing
      };
      if (law.mandatory || law.constitutional || law.tier <= 1) blockers.push(record);
      else advisoryWarnings.push(record);
    }
    if (law.warnings.length) {
      advisoryWarnings.push({ code: 'LAW_WARNINGS', lawId: law.id, warnings: law.warnings });
    }
  }

  if (conflicts.some((conflict) => conflict.material)) {
    blockers.push({ code: 'MATERIAL_LAW_CONFLICT', conflicts: conflicts.filter((item) => item.material) });
  }

  const metrics = governanceMetrics(compiledLaws);
  const simplificationRecommendations = buildSimplificationRecommendations(compiledLaws, metrics);

  let decision = 'PROCEED';
  if (blockers.length) decision = 'HOLD_FOR_HUMAN_REVIEW';
  else if (compiledLaws.some((law) => law.mandatory || law.tier <= 2)) decision = 'PROCEED_WITH_CONTROLS';

  return {
    receiptVersion: '0.1.0',
    generatedAt: new Date().toISOString(),
    task: {
      taskId: context.taskId,
      description: context.description,
      domain: context.domain,
      mode: context.mode,
      riskLevel: context.riskLevel,
      riskScore: context.riskScore,
      authorityLevel: context.authorityLevel,
      reversible: context.reversible,
      affectedParties: context.affectedParties,
      commitments: context.commitments
    },
    decision,
    activeLawSet: compiledLaws,
    activeControlCount: unique(compiledLaws.flatMap((law) => law.controls)).length,
    consideredButInactive,
    conflicts,
    blockers,
    advisoryWarnings,
    governanceMetrics: metrics,
    simplificationRecommendations,
    humanControl: {
      canAppeal: true,
      canRequestAlternativeControl: true,
      canHold: true,
      canStop: true,
      constitutionalBypassAllowed: false
    },
    truthBoundary: 'This receipt proves policy compilation logic ran on supplied inputs. It does not prove the laws are correct, the task is safe, or runtime controls were executed.'
  };
}
