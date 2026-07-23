import test from 'node:test';
import assert from 'node:assert/strict';
import { runPlan } from '../src/plan-runner.mjs';

const cwd = process.cwd();

test('runs multi-step plan successfully', async () => {
  const plan = {
    steps: [
      { type: 'command', cmd: ['node', '-e', "console.log('step1')"] },
      { type: 'command', cmd: ['node', '-e', "console.log('step2')"] }
    ]
  };

  const res = await runPlan({ ...plan, cwd });
  assert.equal(res.success, true);
  assert.equal(res.results.length, 2);
});

test('stops on failure', async () => {
  const plan = {
    steps: [
      { type: 'command', cmd: ['node', '-e', "process.exit(1)"] },
      { type: 'command', cmd: ['node', '-e', "console.log('should not run')"] }
    ]
  };

  const res = await runPlan({ ...plan, cwd });
  assert.equal(res.success, false);
  assert.equal(res.results.length, 1);
});
