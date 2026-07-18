import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { buildFounderProof } from '../src/build-proof.mjs';
import { assertPlatformNeutral } from '../src/semantic-contract.mjs';
import { validateProof } from '../src/validate-proof.mjs';

function build() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'ocode-proof-'));
  const intentPath = path.join(root, 'intent.txt');
  const output = path.join(root, 'proof');
  fs.writeFileSync(intentPath, 'Create a phone-first Dream Intake screen where a dreamer can enter a dream, save it, review a structured Dream Card, correct the interpretation, and receive exactly one next question.');
  const result = buildFounderProof({ intentPath, adapter: 'expo-typescript', outputDirectory: output, generatedAt: '2026-07-18T00:00:00.000Z' });
  return { root, output, result };
}

test('one intent generates the complete founder-proof package', () => {
  const { output } = build();
  assert.equal(validateProof(output).passed, true);
});

test('semantic contract remains adapter and language neutral', () => {
  const { result } = build();
  assert.equal(assertPlatformNeutral(result.contract), true);
  assert.equal(JSON.stringify(result.contract).toLowerCase().includes('expo'), false);
  assert.equal(JSON.stringify(result.contract).toLowerCase().includes('typescript'), false);
});

test('route-fit selects one reversible adapter without permanent architecture lock', () => {
  const { result } = build();
  assert.equal(result.route.selected_adapter, 'expo-typescript');
  assert.equal(result.route.architecture_lock_status, 'NOT_LOCKED_BEYOND_THIS_PROOF');
});

test('law guardian bridge reduces twelve laws to fewer user-facing control groups', () => {
  const { result } = build();
  assert.equal(result.laws.source_law_count, 12);
  assert.ok(result.laws.compiled_control_count < result.laws.source_law_count);
  assert.equal(result.laws.decision, 'PROCEED_WITH_CONTROLS');
});

test('reconstruction preserves every critical behavior in the bounded round trip', () => {
  const { result } = build();
  assert.equal(result.roundTrip.critical_requirements_preserved, true);
  assert.deepEqual(result.roundTrip.missing, []);
  assert.equal(result.reconstructed.reconstructed_behaviors.length, 5);
});

test('generated screen is structurally validated but not overclaimed as device-tested', () => {
  const { result } = build();
  assert.equal(result.sourceValidation.passed, true);
  assert.equal(result.sourceValidation.truth_status, 'STRUCTURALLY_VALIDATED_NOT_BUNDLED');
  assert.equal(result.evidence.claims.device_runtime, 'NOT_RUN_ON_DEVICE');
});

test('continuation package records stop condition and next decision', () => {
  const { output } = build();
  const continuation = fs.readFileSync(path.join(output, 'CONTINUATION.md'), 'utf8');
  assert.match(continuation, /Stop condition/);
  assert.match(continuation, /Next decision/);
  assert.match(continuation, /Do not add screens/);
});

test('unsupported adapter fails closed', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'ocode-proof-'));
  const intentPath = path.join(root, 'intent.txt');
  fs.writeFileSync(intentPath, 'Create a phone-first Dream Intake screen where a dreamer can enter a dream, save it, review a structured Dream Card, correct the interpretation, and receive exactly one next question.');
  assert.throws(() => buildFounderProof({ intentPath, adapter: 'unknown', outputDirectory: path.join(root, 'proof') }), /Adapter must be one of/);
});
