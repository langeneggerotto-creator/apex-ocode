import test from 'node:test';
import assert from 'node:assert/strict';
import { captureSnapshot, restoreSnapshot, computeDiff } from '../src/rollback.mjs';
import { writeFile, readFile } from 'node:fs/promises';
import path from 'node:path';

const workspace = process.cwd();

test('snapshot and restore works', async () => {
  const file = 'test.txt';
  await writeFile(file, 'original');

  const before = await captureSnapshot(workspace, [file]);

  await writeFile(file, 'changed');

  await restoreSnapshot(workspace, before);
  const restored = await readFile(file, 'utf8');

  assert.equal(restored, 'original');
});

test('diff detects changes', () => {
  const before = { a: '1', b: '2' };
  const after = { a: '1', b: '3', c: '4' };

  const diff = computeDiff(before, after);

  assert.deepEqual(diff.modified, ['b']);
  assert.deepEqual(diff.created, ['c']);
  assert.deepEqual(diff.deleted, []);
});
