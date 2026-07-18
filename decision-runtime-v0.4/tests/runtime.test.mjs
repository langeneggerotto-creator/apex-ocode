import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, rm } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  assessCandidateFeasibility,
  assessRouteSet,
  compileActiveLawSet,
  loadRegistry,
  rerankAfterEvidence,
  selectClosestViablePath,
  sha256Text,
  verifyEvidenceRecord,
  writeEvidenceRecord
} from '../src/index.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const context = JSON.parse(await readFile(join(here, '../examples/mobile-only-context.json'), 'utf8'));
const candidates = JSON.parse(await readFile(join(here, '../examples/candidates.json'), 'utf8')).candidates;

function viableCandidate(id, overrides = {}) {
  return {
    id,
    label: id,
    kind: 'vision-facing',
    supportedDevices: ['any'],
    requiredDependencies: [],
    credentialAssumptions: [{ name: 'test credential', status: 'KNOWN' }],
    maintenance: {
      owner: 'test owner',
      recovery: 'restore from source',
      update: 'rerun tests',
      operatingCostStatus: 'known low cost'
    },
    deploymentVerified: false,
    productionValidated: false,
    metrics: {
      directVisionContribution: 8,
      evidenceGain: 8,
      successProbability: 8,
      userEnvironmentFit: 8,
      speedToProof: 8,
      reversibility: 8,
      ownership: 8,
      maintainability: 8,
      reuseValue: 8,
      costBurden: 2,
      complexity: 2,
      dependencyBurden: 2,
      governanceBurden: 2,
      safetyRisk: 2,
      lockIn: 2
    },
    ...overrides
  };
}

const baseContext = {
  vision: 'Prove governed intent-to-implementation portability.',
  currentBarrier: 'bounded test barrier',
  dreamer: { desiredRole: 'founder-controller' },
  environment: { currentDevice: 'iPhone mobile Safari' }
};

test('blocks framework selection until dreamer and environment fit exist', () => {
  assert.throws(() => assessRouteSet({ vision: 'x' }, [viableCandidate('a'), viableCandidate('b')]), /dreamer/);
});

test('requires at least two plausible routes before architecture lock', () => {
  assert.throws(() => assessRouteSet(baseContext, [viableCandidate('a')]), /At least two plausible routes/);
});

test('preserves unsupported credential assumptions as UNKNOWN', () => {
  const result = assessCandidateFeasibility(baseContext, viableCandidate('a', {
    credentialAssumptions: [{ name: 'store account', status: 'UNKNOWN' }]
  }));
  assert.equal(result.feasibilityStatus, 'NEEDS_EVIDENCE');
  assert.ok(result.unknowns.includes('CREDENTIAL_UNKNOWN:store account'));
});

test('does not equate generated or local code with deployment and control', () => {
  const result = assessCandidateFeasibility(baseContext, viableCandidate('a', {
    generatedCodeOnly: true,
    localBuildVerified: true,
    deploymentVerified: false
  }));
  assert.ok(result.warnings.includes('GENERATED_CODE_DOES_NOT_PROVE_DEPLOYMENT_MAINTAINABILITY_OR_FOUNDER_CONTROL'));
  assert.ok(result.warnings.includes('LOCAL_BUILD_DOES_NOT_PROVE_DEPLOYMENT'));
});

test('selects the mobile-first second-adapter route in the current environment', () => {
  const receipt = selectClosestViablePath(context, candidates, { history: context.buildHistory, stopCondition: context.stopCondition });
  assert.equal(receipt.decision, 'PROCEED_WITH_SELECTED_ROUTE');
  assert.equal(receipt.activeRoute.candidateId, 'ocode-v0.4-mobile-first-second-adapter-and-decision-runtime');
  assert.equal(receipt.fallbackRoute.candidateId, 'decision-runtime-only');
  const native = receipt.rankedCandidates.find((item) => item.candidateId === 'wait-for-windows-native-expo-go-test');
  assert.equal(native.viable, false);
  assert.ok(native.disqualifiers.some((value) => value.includes('CURRENT_DEVICE_UNSUPPORTED')));
});

test('rejects a fast route with unacceptable uncontrolled safety risk', () => {
  const unsafe = viableCandidate('unsafe', {
    metrics: { ...viableCandidate('x').metrics, speedToProof: 10, directVisionContribution: 10, safetyRisk: 10 }
  });
  const safe = viableCandidate('safe');
  const receipt = selectClosestViablePath(baseContext, [unsafe, safe]);
  assert.equal(receipt.activeRoute.candidateId, 'safe');
  assert.ok(receipt.rankedCandidates.find((item) => item.candidateId === 'unsafe').disqualifiers.includes('UNACCEPTABLE_UNCONTROLLED_SAFETY_RISK'));
});

test('enforces the two-consecutive-enabling-build detour limit', () => {
  const enabling = viableCandidate('more-plumbing', { kind: 'enabling' });
  const proof = viableCandidate('vision-proof', { kind: 'vision-facing' });
  const receipt = selectClosestViablePath(baseContext, [enabling, proof], {
    history: [{ kind: 'enabling' }, { kind: 'enabling' }]
  });
  assert.equal(receipt.activeRoute.candidateId, 'vision-proof');
  assert.ok(receipt.rankedCandidates.find((item) => item.candidateId === 'more-plumbing').disqualifiers.includes('TWO_BUILD_DETOUR_LIMIT_REQUIRES_VISION_FACING_PROOF'));
});

test('reranks after material environment evidence changes', () => {
  const before = selectClosestViablePath(context, candidates, { history: context.buildHistory });
  const changedContext = {
    ...context,
    environment: { ...context.environment, currentDevice: 'Windows computer with iPhone available', windowsComputerAvailableNow: true }
  };
  const changedCandidates = candidates.map((candidate) => candidate.id === 'wait-for-windows-native-expo-go-test'
    ? {
        ...candidate,
        supportedDevices: ['windows'],
        requiredDependencies: [
          { name: 'Windows computer', status: 'AVAILABLE' },
          { name: 'Expo development server', status: 'VERIFIED' }
        ],
        credentialAssumptions: [{ name: 'Expo Go installation', status: 'KNOWN' }],
        metrics: { ...candidate.metrics, userEnvironmentFit: 10, speedToProof: 10, dependencyBurden: 1, directVisionContribution: 10 }
      }
    : candidate);
  const after = rerankAfterEvidence(before, changedContext, changedCandidates, { history: context.buildHistory });
  assert.equal(after.routeChanged, true);
  assert.equal(after.activeRoute.candidateId, 'wait-for-windows-native-expo-go-test');
});

test('merges duplicate laws into one visible control with traceability', () => {
  const receipt = compileActiveLawSet([
    { id: 'L1', title: 'First', tier: 'MANDATORY', controlKey: 'truth', failureMode: 'false claim', action: 'label claims' },
    { id: 'L2', title: 'Second', tier: 'ADVISORY', controlKey: 'truth', action: 'show status' }
  ], { domain: 'general', riskLevel: 'low', tags: [] });
  assert.equal(receipt.activeControls.length, 1);
  assert.deepEqual(receipt.activeControls[0].sourceLawIds, ['L1', 'L2']);
  assert.equal(receipt.simplificationRecommendations.length, 1);
});

test('rejects binding rules without a named failure mode', () => {
  const receipt = compileActiveLawSet([
    { id: 'L1', title: 'Binding', tier: 'MANDATORY', controlKey: 'x', action: 'do x' }
  ], { domain: 'general', riskLevel: 'low', tags: [] });
  assert.equal(receipt.activeControls.length, 0);
  assert.ok(receipt.rejected[0].errors.includes('BINDING_RULE_REQUIRES_NAMED_FAILURE_MODE'));
});

test('requires expiry or review for temporary rules', () => {
  const receipt = compileActiveLawSet([
    { id: 'T1', title: 'Temporary', tier: 'TEMPORARY', controlKey: 'temporary', failureMode: 'stale control', action: 'review it' }
  ], { domain: 'general', riskLevel: 'low', tags: [] });
  assert.ok(receipt.rejected[0].errors.includes('TEMPORARY_RULE_REQUIRES_EXPIRY_OR_REVIEW'));
});

test('does not downgrade mandatory controls merely to reduce burden', () => {
  const receipt = compileActiveLawSet([
    { id: 'M1', title: 'Mandatory', tier: 'MANDATORY', controlKey: 'safety', failureMode: 'harm', action: 'hold' }
  ], { domain: 'general', riskLevel: 'high', tags: [] }, {
    requestedDowngrades: [{ controlKey: 'safety', reason: 'reduce burden' }]
  });
  assert.ok(receipt.rejected.some((item) => item.errors.includes('MANDATORY_CONTROL_CANNOT_BE_DOWNGRADED_MERELY_TO_REDUCE_BURDEN')));
});

test('makes unresolved material conflicts visible and holds', () => {
  const receipt = compileActiveLawSet([
    { id: 'A', title: 'A', tier: 'MANDATORY', controlKey: 'a', failureMode: 'x', action: 'a', conflictGroup: 'release', requiredOutcome: 'ALLOW' },
    { id: 'B', title: 'B', tier: 'MANDATORY', controlKey: 'b', failureMode: 'y', action: 'b', conflictGroup: 'release', requiredOutcome: 'DENY' }
  ], { domain: 'general', riskLevel: 'high', tags: [] });
  assert.equal(receipt.decision, 'HOLD_FOR_HUMAN_CONFLICT_RESOLUTION');
  assert.equal(receipt.conflicts[0].resolution, 'HUMAN_DECISION_REQUIRED');
});

test('writes and verifies an atomic Evidence Ledger-compatible record', async () => {
  const path = join(tmpdir(), `ocode-evidence-${process.pid}-${Date.now()}.json`);
  try {
    const written = await writeEvidenceRecord(path, { evidenceType: 'TEST', claim: 'bounded claim' });
    assert.equal(verifyEvidenceRecord(written.record).valid, true);
    assert.match(written.fileDigest, /^sha256:/);
  } finally {
    await rm(path, { force: true });
  }
});

test('loads an authenticated HTTP registry and verifies a pinned digest', async () => {
  const raw = JSON.stringify({ laws: [{ id: 'L1' }] });
  let authorization = null;
  const server = createServer((request, response) => {
    authorization = request.headers.authorization;
    response.writeHead(200, { 'content-type': 'application/json' });
    response.end(raw);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  try {
    const address = server.address();
    const result = await loadRegistry(`http://127.0.0.1:${address.port}/registry`, {
      token: 'test-token',
      expectedDigest: sha256Text(raw)
    });
    assert.equal(authorization, 'Bearer test-token');
    assert.equal(result.authenticatedRequest, true);
    assert.equal(result.provenanceStatus, 'PINNED_MATCH');
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('reports registry drift instead of silently accepting it', async () => {
  const raw = JSON.stringify({ laws: [{ id: 'CHANGED' }] });
  const server = createServer((_request, response) => {
    response.writeHead(200, { 'content-type': 'application/json' });
    response.end(raw);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  try {
    const address = server.address();
    const result = await loadRegistry(`http://127.0.0.1:${address.port}/registry`, {
      expectedDigest: '0'.repeat(64)
    });
    assert.equal(result.provenanceStatus, 'DRIFT_DETECTED');
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
