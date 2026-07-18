import test from 'node:test';
import assert from 'node:assert/strict';
import {
  assertPlatformNeutral,
  extractManifest,
  generateExpoSource,
  generateModelSource,
  generateWebSource,
  parseIntent,
  REQUIRED_BEHAVIORS,
  REQUIRED_FIELDS
} from '../src/compiler.mjs';

const intent = 'Create a phone-first Decision Clarity screen where a person can describe a decision, enter two options and one constraint, save the draft, review a structured Decision Card, correct the interpretation, select a current preference, and receive exactly one next question.';

test('parses the second natural-language intent into a platform-neutral semantic contract', () => {
  const { contract } = parseIntent(intent);
  assert.equal(contract.contractId, 'decision-clarity-second-intent-v0.5');
  assert.deepEqual(contract.fields.map((field) => field.id), REQUIRED_FIELDS);
  assert.deepEqual(contract.behaviors, REQUIRED_BEHAVIORS);
  assert.equal(contract.nextQuestion.count, 1);
  assert.equal(assertPlatformNeutral(contract), true);
});

test('rejects an intent missing material Decision Clarity behavior', () => {
  assert.throws(() => parseIntent('Create a phone-first Decision Clarity screen with two options.'), /missing required meaning/i);
});

test('produces independent adapter manifests with the same fields and behaviors', () => {
  const { contract } = parseIntent(intent);
  const expo = extractManifest(generateExpoSource(contract));
  const web = extractManifest(generateWebSource(contract));
  assert.equal(expo.kind, 'expo-typescript-screen');
  assert.equal(web.kind, 'mobile-web-screen');
  assert.deepEqual(expo.fields, web.fields);
  assert.deepEqual(expo.behaviors, web.behaviors);
  assert.equal(expo.nextQuestionCount, 1);
  assert.equal(web.nextQuestionCount, 1);
});

test('generates a shared model manifest tied to the same semantic contract', () => {
  const { contract } = parseIntent(intent);
  const model = extractManifest(generateModelSource(contract));
  assert.equal(model.kind, 'shared-model');
  assert.equal(model.contractId, contract.contractId);
  assert.deepEqual(model.fields, REQUIRED_FIELDS);
  assert.deepEqual(model.behaviors, REQUIRED_BEHAVIORS);
});

test('keeps target-framework terms out of the semantic contract', () => {
  const { contract } = parseIntent(intent);
  const text = JSON.stringify(contract).toLowerCase();
  for (const forbidden of ['expo', 'typescript', 'react native', 'html', 'javascript', 'asyncstorage', 'localstorage']) {
    assert.equal(text.includes(forbidden), false, 'contract leaked ' + forbidden);
  }
});
