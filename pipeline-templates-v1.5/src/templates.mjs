export const templates = {
  'node-ci': {
    steps: [
      { type: 'command', cmd: ['npm', 'install'] },
      { type: 'command', cmd: ['npm', 'test'] },
      { type: 'command', cmd: ['npm', 'build'] }
    ]
  },
  'python-ci': {
    steps: [
      { type: 'command', cmd: ['pip', 'install', '-r', 'requirements.txt'] },
      { type: 'command', cmd: ['pytest'] }
    ]
  },
  'generic-build': {
    steps: [
      { type: 'command', cmd: ['make'] }
    ]
  }
};

export function getTemplate(name) {
  if (!templates[name]) {
    throw new Error('Unknown template');
  }
  return templates[name];
}
