import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';

export function runIsolated({ cmd, cwd, timeoutMs = 5000, maxOutputBytes = 65536 }) {
  const containerName = `ocode-${randomUUID()}`;

  const dockerArgs = [
    'run', '--rm',
    '--name', containerName,
    '--network=none',
    '--memory=256m',
    '--cpus=0.5',
    '--pids-limit=64',
    '--read-only',
    '-v', `${cwd}:/workspace:ro`,
    '-w', '/workspace',
    'node:22',
    ...cmd
  ];

  const proc = spawn('docker', dockerArgs, {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: {}
  });

  let stdout = '';
  let stderr = '';
  let killed = false;

  const kill = () => {
    if (!killed) {
      killed = true;
      spawn('docker', ['kill', containerName]);
    }
  };

  const timer = setTimeout(() => kill(), timeoutMs);

  proc.stdout.on('data', (d) => {
    stdout += d.toString();
    if (stdout.length > maxOutputBytes) {
      stdout = stdout.slice(0, maxOutputBytes);
      kill();
    }
  });

  proc.stderr.on('data', (d) => {
    stderr += d.toString();
    if (stderr.length > maxOutputBytes) {
      stderr = stderr.slice(0, maxOutputBytes);
      kill();
    }
  });

  return new Promise((resolve) => {
    proc.on('close', (code) => {
      clearTimeout(timer);
      resolve({ code, stdout, stderr, killed });
    });
  });
}
