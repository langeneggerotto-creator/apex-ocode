import test from 'node:test';
import assert from 'node:assert/strict';
import { generateGitHubActions } from '../src/github-actions-exporter.mjs';

test('generates valid yaml structure', () => {
  const yaml = generateGitHubActions('test', [
    { cmd: ['npm', 'install'] },
    { cmd: ['npm', 'test'] }
  ]);

  assert.ok(yaml.includes('name: OCode Pipeline'));
  assert.ok(yaml.includes('npm install'));
  assert.ok(yaml.includes('npm test'));
});
