export function generateGitHubActions(planName, steps) {
  return `name: OCode Pipeline - ${planName}

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '22'

${steps.map((s, i) => `      - name: Step ${i+1}\n        run: ${s.cmd.join(' ')}`).join('\n')}
`;
}
