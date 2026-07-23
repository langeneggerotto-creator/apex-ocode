import test from 'node:test';
import assert from 'node:assert/strict';
import { applyEnv, redactOutput } from '../src/env-layer.mjs';

test('applies variables and secrets correctly', () => {
  const res = applyEnv({
    variables: { NODE_ENV: 'prod' },
    secrets: { API_KEY: '12345' }
  });

  assert.equal(res.runtimeEnv.API_KEY, '12345');
  assert.equal(res.maskedView.API_KEY, '***');
});

test('redacts secrets from output', () => {
  const output = 'key=12345';
  const redacted = redactOutput(output, { API_KEY: '12345' });
  assert.equal(redacted, 'key=***');
});
