import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { runPlanWithRollback } from '../src/plan-with-rollback.mjs';

const cwd = process.cwd();
const testFile = path.join(cwd, 'rollback-test.txt');

test('auto rollback restores file on failure', async () => {
  await fs.writeFile(testFile, 'original');

  const plan = {
    steps: [
      { type: 'command', cmd: ['node', '-e', "require('fs').writeFileSync('rollback-test.txt','changed')"] },
      { type: 'command', cmd: ['node', '-e', "process.exit(1)"] }
    ]
  };

  const res = await runPlanWithRollback({ ...plan, cwd });

  const content = await fs.readFile(testFile, 'utf8');

  assert.equal(res.success, false);
  assert.equal(res.rolledBack, true);
  assert.equal(content, 'original');
});
