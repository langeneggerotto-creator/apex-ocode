import assert from 'node:assert/strict';
import { mkdtemp, readFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import {
  TerminalSessionStore,
  inspectCommand,
  resolveWorkspacePath
} from '../src/terminal-session.mjs';

async function fixture() {
  const root = await mkdtemp(path.join(os.tmpdir(), 'ocode-terminal-v06-'));
  let tick = 0;
  const store = new TerminalSessionStore({
    workspaceRoot: root,
    stateFile: path.join(root, '.ocode', 'terminal-sessions.json'),
    clock: () => `2026-07-22T00:00:${String(tick++).padStart(2, '0')}.000Z`,
    idFactory: () => 'session-001'
  });
  await store.load();
  return { root, store };
}

test('creates, persists, and reloads an active session', async () => {
  const { root, store } = await fixture();
  const created = await store.createSession({ cwd: '.', shell: 'sh' });

  assert.equal(created.id, 'session-001');
  assert.equal(created.status, 'ACTIVE');
  assert.equal(created.cwd, root);

  const reloaded = new TerminalSessionStore({
    workspaceRoot: root,
    stateFile: path.join(root, '.ocode', 'terminal-sessions.json')
  });
  await reloaded.load();
  assert.equal(reloaded.getSession('session-001').status, 'ACTIVE');
});

test('denies terminal working directories outside the trusted workspace', () => {
  assert.throws(
    () => resolveWorkspacePath('/workspace/project', '../secrets'),
    /escapes the trusted workspace/u
  );
  assert.throws(
    () => resolveWorkspacePath('/workspace/project', '/tmp'),
    /Absolute terminal working directories are denied/u
  );
});

test('allows only simple commands with allowlisted executables', () => {
  assert.deepEqual(inspectCommand('npm test'), {
    allowed: true,
    reason: 'ALLOWLIST_MATCH',
    executable: 'npm'
  });
  assert.equal(inspectCommand('curl example.com').reason, 'EXECUTABLE_NOT_ALLOWLISTED');
  assert.equal(inspectCommand('npm test && rm -rf .').reason, 'SHELL_CONTROL_SYNTAX_DENIED');
});

test('records command admission and transcript without executing a process', async () => {
  const { store } = await fixture();
  await store.createSession();

  const allowed = await store.admitCommand('session-001', 'npm test');
  const denied = await store.admitCommand('session-001', 'curl example.com');
  const output = await store.appendOutput('session-001', {
    stream: 'stdout',
    text: '82 tests passed'
  });

  assert.equal(allowed.decision, 'ALLOW');
  assert.equal(denied.decision, 'DENY');
  assert.equal(output.sequence, 1);
  assert.equal(store.getSession('session-001').transcript[0].text, '82 tests passed');
});

test('closed sessions reject additional commands and output', async () => {
  const { store } = await fixture();
  await store.createSession();
  await store.closeSession('session-001');

  await assert.rejects(
    store.admitCommand('session-001', 'npm test'),
    /not active/u
  );
  await assert.rejects(
    store.appendOutput('session-001', { text: 'late output' }),
    /not active/u
  );
});

test('event evidence is hash-linked and persisted as valid JSON', async () => {
  const { root, store } = await fixture();
  await store.createSession();
  await store.admitCommand('session-001', 'node --version');
  await store.closeSession('session-001');

  assert.equal(store.verifyEventChain(), true);
  const persisted = JSON.parse(await readFile(
    path.join(root, '.ocode', 'terminal-sessions.json'),
    'utf8'
  ));
  assert.equal(persisted.events.length, 3);
  assert.equal(persisted.events[1].previousHash, persisted.events[0].hash);
});
