import test from 'node:test';
import assert from 'node:assert/strict';
import { compilePolicy, normalizeLaw } from '../src/law-guardian.mjs';

const truthLaw = {
  id: 'TRUTH', title: 'Truth', tier: 0, constitutional: true, mandatory: true,
  domains: ['*'], modes: ['*'], riskLevels: ['*'],
  failureMode: 'Claims exceed evidence.', protectedValue: 'Truth',
  controls: ['Record truth boundary.'], requiredEvidence: ['truth'],
  mergeKey: 'TRUTH', burden: 1, protection: 5
};

function context(overrides = {}) {
  return {
    taskId: 'T-1', domain: 'SOFTWARE', mode: 'PROTOTYPE', riskLevel: 'LOW',
    reversible: true, affectedParties: 1, evidence: { truth: true }, ...overrides
  };
}

test('low-risk reversible prototype receives a minimum active set, not production controls', () => {
  const laws = [
    truthLaw,
    {
      id: 'PROTO', title: 'Prototype', tier: 3, domains: ['SOFTWARE'], modes: ['PROTOTYPE'],
      riskLevels: ['LOW'], failureMode: 'Prototype escapes bounds.', controls: ['Set stop condition.'],
      mergeKey: 'PROTO', burden: 1, protection: 3
    },
    {
      id: 'PROD', title: 'Production', tier: 2, domains: ['SOFTWARE'], modes: ['PRODUCTION'],
      riskLevels: ['HIGH'], failureMode: 'Production cannot recover.', controls: ['Run restore test.'],
      requiredEvidence: ['restore'], mergeKey: 'PROD', burden: 5, protection: 6
    }
  ];
  const receipt = compilePolicy(laws, context());
  assert.equal(receipt.decision, 'PROCEED_WITH_CONTROLS');
  assert.deepEqual(receipt.activeLawSet.flatMap((law) => law.sourceLawIds).sort(), ['PROTO', 'TRUTH']);
  assert.ok(receipt.consideredButInactive.some((item) => item.id === 'PROD'));
});

test('high-stakes constitutional protection cannot be removed to reduce burden', () => {
  const laws = [
    truthLaw,
    {
      id: 'QUALIFIED', title: 'Qualified review', tier: 0, constitutional: true, mandatory: true,
      domains: ['MEDICAL'], modes: ['HIGH_STAKES'], riskLevels: ['CRITICAL'],
      failureMode: 'Unsafe unqualified action.', controls: ['Require qualified review.'],
      requiredEvidence: ['qualified'], mergeKey: 'QUALIFIED', burden: 9, protection: 10
    }
  ];
  const receipt = compilePolicy(laws, context({
    domain: 'MEDICAL', mode: 'HIGH_STAKES', riskLevel: 'CRITICAL', reversible: false,
    evidence: { truth: true, qualified: false }
  }));
  assert.equal(receipt.decision, 'HOLD_FOR_HUMAN_REVIEW');
  assert.ok(receipt.activeLawSet.some((law) => law.sourceLawIds.includes('QUALIFIED')));
  assert.ok(receipt.blockers.some((blocker) => blocker.code === 'MISSING_REQUIRED_EVIDENCE'));
});

test('duplicate laws compile to one user-facing control group with traceability', () => {
  const laws = [
    truthLaw,
    {
      id: 'TRUTH-2', title: 'No proof no promotion', tier: 1, mandatory: true,
      domains: ['*'], modes: ['*'], riskLevels: ['*'], failureMode: 'Unsupported promotion.',
      controls: ['Require evidence receipt.'], requiredEvidence: ['truth'],
      mergeKey: 'TRUTH', burden: 2, protection: 5
    }
  ];
  const receipt = compilePolicy(laws, context());
  assert.equal(receipt.activeLawSet.length, 1);
  assert.deepEqual(receipt.activeLawSet[0].sourceLawIds.sort(), ['TRUTH', 'TRUTH-2']);
  assert.equal(receipt.activeLawSet[0].controls.length, 2);
});

test('binding nonmandatory rule without a failure mode is downgraded to advisory', () => {
  const law = normalizeLaw({
    id: 'EMPTY-RATIONALE', title: 'Empty', tier: 2, domains: ['*'], modes: ['*'], riskLevels: ['*']
  });
  assert.equal(law.tier, 5);
  assert.ok(law.warnings.includes('DOWNGRADED_TO_ADVISORY_NO_FAILURE_MODE'));
});

test('expired temporary rules do not activate', () => {
  const laws = [truthLaw, {
    id: 'TEMP', title: 'Temporary', tier: 4, domains: ['*'], modes: ['*'], riskLevels: ['*'],
    failureMode: 'Temporary incident recurs.', controls: ['Extra review.'], expiryDate: '2020-01-01',
    mergeKey: 'TEMP', burden: 2, protection: 2
  }];
  const receipt = compilePolicy(laws, context(), { now: '2026-07-17T00:00:00Z' });
  assert.ok(!receipt.activeLawSet.some((law) => law.sourceLawIds.includes('TEMP')));
  assert.ok(receipt.consideredButInactive.some((item) => item.id === 'TEMP' && item.reasons.includes('EXPIRED')));
});

test('material conflicts are visible and require human review', () => {
  const laws = [
    truthLaw,
    {
      id: 'A', title: 'A', tier: 1, mandatory: true, domains: ['*'], modes: ['*'], riskLevels: ['*'],
      failureMode: 'A failure.', controls: ['Do A.'], conflictsWith: ['B'], mergeKey: 'A', burden: 1, protection: 2
    },
    {
      id: 'B', title: 'B', tier: 1, mandatory: true, domains: ['*'], modes: ['*'], riskLevels: ['*'],
      failureMode: 'B failure.', controls: ['Do B.'], conflictsWith: ['A'], mergeKey: 'B', burden: 1, protection: 2
    }
  ];
  const receipt = compilePolicy(laws, context());
  assert.equal(receipt.decision, 'HOLD_FOR_HUMAN_REVIEW');
  assert.equal(receipt.conflicts.length, 1);
  assert.ok(receipt.blockers.some((blocker) => blocker.code === 'MATERIAL_LAW_CONFLICT'));
});

test('unknown risk is never treated as ready', () => {
  const receipt = compilePolicy([truthLaw], context({ riskLevel: 'not-specified' }));
  assert.equal(receipt.task.riskLevel, 'UNKNOWN');
  assert.equal(receipt.decision, 'HOLD_FOR_HUMAN_REVIEW');
  assert.ok(receipt.blockers.some((blocker) => blocker.code === 'UNKNOWN_RISK_NOT_READY'));
});

test('receipt exposes active controls, inactive laws, metrics, and human appeal', () => {
  const receipt = compilePolicy([truthLaw], context());
  assert.equal(receipt.activeControlCount, 1);
  assert.ok(receipt.governanceMetrics.protection >= receipt.governanceMetrics.burden);
  assert.equal(receipt.humanControl.canAppeal, true);
  assert.equal(receipt.humanControl.constitutionalBypassAllowed, false);
  assert.match(receipt.truthBoundary, /does not prove/i);
});
