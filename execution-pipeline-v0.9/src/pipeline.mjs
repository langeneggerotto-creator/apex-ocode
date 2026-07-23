import { createHash } from 'node:crypto';
import { inspectCommand } from '../../terminal-session-v0.6/src/terminal-session.mjs';
import { runIsolated } from '../../process-runner-v0.8/src/docker-runner.mjs';

function sha256(x) {
  return createHash('sha256').update(JSON.stringify(x)).digest('hex');
}

export async function executePipeline({ sessionStore, sessionId, command, cwd }) {
  const admission = inspectCommand(command.join(' '));

  const record = {
    command,
    decision: admission.allowed ? 'ALLOW' : 'DENY',
    reason: admission.reason,
    execution: null,
    output: null,
    durationMs: 0,
    evidenceHash: null
  };

  if (!admission.allowed) {
    record.evidenceHash = sha256(record);
    return record;
  }

  const start = Date.now();

  const result = await runIsolated({
    cmd: command,
    cwd
  });

  const duration = Date.now() - start;

  record.execution = {
    exitCode: result.code,
    killed: result.killed
  };

  record.output = {
    stdout: result.stdout,
    stderr: result.stderr
  };

  record.durationMs = duration;
  record.evidenceHash = sha256(record);

  if (sessionStore) {
    await sessionStore.appendOutput(sessionId, {
      text: JSON.stringify(record)
    });
  }

  return record;
}
