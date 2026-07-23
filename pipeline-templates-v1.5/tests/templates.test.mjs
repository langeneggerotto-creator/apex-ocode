import test from 'node:test';
import assert from 'node:assert/strict';
import { getTemplate } from '../src/templates.mjs';

test('loads node-ci template', () => {
  const tpl = getTemplate('node-ci');
  assert.equal(tpl.steps.length, 3);
});

test('throws on unknown template', () => {
  assert.throws(() => getTemplate('unknown'));
});
