import test from 'node:test';
import assert from 'node:assert/strict';
import { runIsolated } from '../src/docker-runner.mjs';

const cwd = process.cwd();

test('executes simple command', async () => {
  const res = await runIsolated({ cmd: ['node', '-e', "console.log('ok')"], cwd });
  assert.equal(res.code, 0);
  assert.match(res.stdout, /ok/);
});

test('blocks network', async () => {
  const res = await runIsolated({ cmd: ['node', '-e', "require('http').get('http://example.com')"], cwd });
  assert.notEqual(res.code, 0);
});

test('enforces timeout', async () => {
  const res = await runIsolated({ cmd: ['node', '-e', "while(true){}"], cwd, timeoutMs: 1000 });
  assert.equal(res.killed, true);
});

test('enforces output limit', async () => {
  const res = await runIsolated({ cmd: ['node', '-e', "console.log('x'.repeat(100000))"], cwd, maxOutputBytes: 1000 });
  assert.ok(res.stdout.length <= 1000);
});
