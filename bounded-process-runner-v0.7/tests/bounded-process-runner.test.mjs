import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, symlink, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { TerminalSessionStore } from '../../terminal-session-v0.6/src/terminal-session.mjs';
import { BoundedProcessRunner } from '../src/bounded-process-runner.mjs';

async function fixture(options = {}) {
  const parent = await mkdtemp(path.join(os.tmpdir(), 'ocode-runner-test-'));
  const workspace = path.join(parent, 'workspace');
  await mkdir(workspace);
  const store = new TerminalSessionStore({
    workspaceRoot: workspace,
    stateFile: path.join(workspace, '.ocode', 'sessions.json'),
    idFactory: () => 'session-001'
  });
  await store.load();
  const session = await store.createSession();
  const runner = new BoundedProcessRunner({
    workspaceRoot: workspace,
    sessionStore: store,
    timeoutMs: options.timeoutMs ?? 2_000,
    outputLimitBytes: options.outputLimitBytes ?? 8_192,
    killGraceMs: 50
  });
  return { parent, workspace, store, sessionId: session.id, runner };
}

async function writeScript(workspace, name, source) {
  const file = path.join(workspace, name);
  await writeFile(file, source, 'utf8');
  return file;
}

test('runs one admitted process inside the bounded workspace sandbox', async () => {
  const { workspace, store, sessionId, runner } = await fixture();
  await writeScript(workspace, 'success.mjs', `
    import { writeFileSync } from 'node:fs';
    console.log('cwd=' + process.cwd());
    writeFileSync('created.txt', 'created inside workspace');
  `);

  const result = await runner.run({
    sessionId,
    executable: 'node',
    args: ['success.mjs']
  });

  assert.equal(result.status, 'COMPLETED');
  assert.equal(result.exitCode, 0);
  assert.match(result.stdout, /cwd=\/workspace/u);
  assert.equal(await readFile(path.join(workspace, 'created.txt'), 'utf8'), 'created inside workspace');
  assert.equal(result.network, 'DENIED_BY_LINUX_NETWORK_NAMESPACE');
  assert.match(result.sandbox, /CHROOT/u);
  assert.ok(store.getSession(sessionId).transcript.length >= 2);
});

test('denies requested network inheritance before spawning', async () => {
  const { sessionId, runner } = await fixture();
  await assert.rejects(
    runner.run({ sessionId, executable: 'node', args: ['--version'], network: 'inherit' }),
    /NETWORK_POLICY_DENIED/u
  );
});

test('network namespace prevents external network access', async () => {
  const { workspace, sessionId, runner } = await fixture({ timeoutMs: 4_000 });
  await writeScript(workspace, 'network.mjs', `
    try {
      await fetch('https://example.com', { signal: AbortSignal.timeout(1000) });
      console.log('NETWORK_UNEXPECTEDLY_AVAILABLE');
      process.exitCode = 9;
    } catch (error) {
      console.log('NETWORK_DENIED');
    }
  `);

  const result = await runner.run({ sessionId, executable: 'node', args: ['network.mjs'] });
  assert.equal(result.status, 'COMPLETED');
  assert.match(result.stdout, /NETWORK_DENIED/u);
  assert.doesNotMatch(result.stdout, /NETWORK_UNEXPECTEDLY_AVAILABLE/u);
});

test('chroot prevents reading an absolute host path outside the workspace', async () => {
  const { parent, workspace, sessionId, runner } = await fixture();
  const secret = path.join(parent, 'outside-secret.txt');
  await writeFile(secret, 'must not be readable', 'utf8');
  await writeScript(workspace, 'escape.mjs', `
    import { readFileSync } from 'node:fs';
    try {
      readFileSync(${JSON.stringify(secret)}, 'utf8');
      console.log('ESCAPE_SUCCEEDED');
      process.exitCode = 7;
    } catch (error) {
      console.log('ESCAPE_DENIED:' + error.code);
    }
  `);

  const result = await runner.run({ sessionId, executable: 'node', args: ['escape.mjs'] });
  assert.equal(result.status, 'COMPLETED');
  assert.match(result.stdout, /ESCAPE_DENIED:ENOENT/u);
});

test('rejects a working-directory symlink that physically escapes the workspace', async () => {
  const { parent, workspace, sessionId, runner } = await fixture();
  const outside = path.join(parent, 'outside-dir');
  await mkdir(outside);
  await symlink(outside, path.join(workspace, 'escape-link'));

  await assert.rejects(
    runner.run({ sessionId, executable: 'node', args: ['--version'], cwd: 'escape-link' }),
    /escapes the physical workspace/u
  );
});

test('terminates a process when the timeout expires', async () => {
  const { workspace, sessionId, runner } = await fixture({ timeoutMs: 150 });
  await writeScript(workspace, 'slow.mjs', `setInterval(() => {}, 1000);`);

  const result = await runner.run({ sessionId, executable: 'node', args: ['slow.mjs'] });
  assert.equal(result.status, 'TIMED_OUT');
  assert.ok(result.durationMs < 2_000);
});

test('cancels a running process through AbortSignal', async () => {
  const { workspace, sessionId, runner } = await fixture({ timeoutMs: 5_000 });
  await writeScript(workspace, 'cancel.mjs', `setInterval(() => {}, 1000);`);
  const controller = new AbortController();
  setTimeout(() => controller.abort(), 100);

  const result = await runner.run({
    sessionId,
    executable: 'node',
    args: ['cancel.mjs'],
    signal: controller.signal
  });
  assert.equal(result.status, 'CANCELLED');
});

test('stops output at the configured combined byte limit', async () => {
  const { workspace, sessionId, runner } = await fixture({ outputLimitBytes: 1_024 });
  await writeScript(workspace, 'loud.mjs', `
    const chunk = 'x'.repeat(512);
    setInterval(() => process.stdout.write(chunk), 1);
  `);

  const result = await runner.run({ sessionId, executable: 'node', args: ['loud.mjs'] });
  assert.equal(result.status, 'OUTPUT_LIMIT_EXCEEDED');
  assert.equal(Buffer.byteLength(result.stdout) + Buffer.byteLength(result.stderr), 1_024);
  assert.equal(result.outputTruncated, true);
  assert.ok(result.outputBytes > 1_024);
});

test('returns POLICY_DENIED without spawning a non-allowlisted executable', async () => {
  const { sessionId, runner } = await fixture();
  const result = await runner.run({ sessionId, executable: 'curl', args: ['https://example.com'] });
  assert.equal(result.status, 'POLICY_DENIED');
  assert.equal(result.sandbox, 'NOT_STARTED');
});
