import { runIsolated } from '../../process-runner-v0.8/src/docker-runner.mjs';

export async function runPlan({ steps, cwd }) {
  const results = [];

  for (const step of steps) {
    if (step.type !== 'command') {
      throw new Error('Unsupported step type');
    }

    const start = Date.now();
    const res = await runIsolated({ cmd: step.cmd, cwd });
    const duration = Date.now() - start;

    const record = {
      cmd: step.cmd,
      code: res.code,
      stdout: res.stdout,
      stderr: res.stderr,
      killed: res.killed,
      duration
    };

    results.push(record);

    if (res.code !== 0) {
      return {
        success: false,
        failedStep: step,
        results
      };
    }
  }

  return {
    success: true,
    results
  };
}
