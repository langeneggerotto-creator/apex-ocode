import { spawnSync } from 'node:child_process';

export function gitStatus(cwd) {
  const res = spawnSync('git', ['status', '--porcelain'], { cwd });
  return res.stdout.toString();
}

export function gitBranch(cwd) {
  const res = spawnSync('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { cwd });
  return res.stdout.toString().trim();
}

export function gitCommit(cwd, message = 'ocode:auto-commit') {
  spawnSync('git', ['add', '.'], { cwd });
  return spawnSync('git', ['commit', '-m', message], { cwd }).status;
}

export function gitDiff(cwd) {
  const res = spawnSync('git', ['diff'], { cwd });
  return res.stdout.toString();
}
