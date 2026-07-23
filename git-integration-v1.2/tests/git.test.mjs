import test from 'node:test';
import assert from 'node:assert/strict';
import { gitStatus, gitBranch } from '../src/git-layer.mjs';

const cwd = process.cwd();

test('detects git branch', () => {
  const branch = gitBranch(cwd);
  assert.ok(branch.length > 0);
});

test('returns git status', () => {
  const status = gitStatus(cwd);
  assert.ok(typeof status === 'string');
});
