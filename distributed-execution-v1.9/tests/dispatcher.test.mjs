import test from 'node:test';
import assert from 'node:assert/strict';
import { Dispatcher } from '../src/dispatcher.mjs';

const mockWorker = {
  run: async (step) => ({ success: true, step })
};

test('dispatches steps across workers', async () => {
  const dispatcher = new Dispatcher([mockWorker, mockWorker]);

  const plan = {
    steps: [
      { cmd: ['echo', '1'] },
      { cmd: ['echo', '2'] }
    ]
  };

  const res = await dispatcher.dispatch(plan);
  assert.equal(res.success, true);
  assert.equal(res.results.length, 2);
});
