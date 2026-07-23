import test from 'node:test';
import assert from 'node:assert/strict';
import { executePipeline } from '../src/pipeline.mjs';

test('denied command does not execute', async () => {
  const res = await executePipeline({ command: ['curl','example.com'] });
  assert.equal(res.decision, 'DENY');
});

test('allowed command executes and returns output', async () => {
  const res = await executePipeline({ command: ['node','-e','console.log("ok")'], cwd: process.cwd() });
  assert.equal(res.decision, 'ALLOW');
  assert.match(res.output.stdout, /ok/);
});
