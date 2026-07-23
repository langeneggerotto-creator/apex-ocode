import { runPlan } from '../../execution-plans-v1.3/src/plan-runner.mjs';
import { snapshotWorkspace, restoreWorkspace } from '../../workspace-snapshot-v1.0/src/snapshot.mjs';

export async function runPlanWithRollback({ steps, cwd }) {
  const preSnapshot = await snapshotWorkspace(cwd);

  const result = await runPlan({ steps, cwd });

  if (!result.success) {
    await restoreWorkspace(cwd, preSnapshot);
    return {
      ...result,
      rolledBack: true
    };
  }

  return {
    ...result,
    rolledBack: false
  };
}
