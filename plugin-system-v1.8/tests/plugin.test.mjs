import test from 'node:test';
import assert from 'node:assert/strict';
import { registerPlugin, runWithPlugins } from '../src/plugin-system.mjs';

let called = false;

registerPlugin({
  name: 'test-plugin',
  hooks: {
    beforeRun: async () => { called = true; }
  }
});

test('plugin beforeRun hook executes', async () => {
  const result = await runWithPlugins({
    beforeRunContext: {},
    afterRunContext: {},
    run: async () => ({ success: true })
  });

  assert.equal(called, true);
  assert.equal(result.success, true);
});
