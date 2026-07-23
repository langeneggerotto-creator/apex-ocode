import { spawn } from 'node:child_process';
import { resolveWorkspacePath } from '../../terminal-session-v0.6/src/terminal-session.mjs';

export class BoundedProcessRunner {
  constructor({ workspaceRoot, timeoutMs = 5000, maxOutputBytes = 65536 } = {}) {
    this.workspaceRoot = workspaceRoot;
    this.timeoutMs = timeoutMs;
    this.maxOutputBytes = maxOutputBytes;
  }

  run({ command, args = [], cwd = '.' }) {
    const resolvedCwd = resolveWorkspacePath(this.workspaceRoot, cwd);

    return new Promise((resolve, reject) => {
      const child = spawn(command, args, {
        cwd: resolvedCwd,
        shell: false,
        env: {}
      });

      let stdout = '';
      let stderr = '';
      let killed = false;

      const timeout = setTimeout(() => {
        killed = true;
        child.kill('SIGKILL');
      }, this.timeoutMs);

      child.stdout.on('data', (data) => {
        if (stdout.length < this.maxOutputBytes) {
          stdout += data.toString();
        }
      });

      child.stderr.on('data', (data) => {
        if (stderr.length < this.maxOutputBytes) {
          stderr += data.toString();
        }
      });

      child.on('close', (code) => {
        clearTimeout(timeout);
        resolve({
          code,
          stdout,
          stderr,
          killed
        });
      });

      child.on('error', (err) => {
        clearTimeout(timeout);
        reject(err);
      });
    });
  }
}
