import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { BoundedProcessRunner } from '../src/process-runner.mjs';

test('runs simple command within workspace', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'ocode-runner-'));
  const runner = new BoundedProcessRunner({ workspaceRoot: root });

  const result = await runner.run({ command: 'node', args: ['-e', 'console.log("ok")'] });

  assert.equal(result.code, 0);
  assert.match(result.stdout, /ok/);
});

test('enforces timeout', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'ocode-runner-'));
  const runner = new BoundedProcessRunner({ workspaceRoot: root, timeoutMs: 100 });

  const result = await runner.run({ command: 'node', args: ['-e', 'setTimeout(()=>{},1000)'] });

  assert.equal(result.killed, true);
});

test('limits output size', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'ocode-runner-'));
  const runner = new BoundedProcessRunner({ workspaceRoot: root, maxOutputBytes: 10 });

  const result = await runner.run({ command: 'node', args: ['-e', 'console.log("123456789012345")'] });

  assert.ok(result.stdout.length <= 10);
});
