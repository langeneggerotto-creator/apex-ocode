const plugins = [];

export function registerPlugin(plugin) {
  if (!plugin || !plugin.name) {
    throw new Error('Invalid plugin');
  }
  plugins.push(plugin);
}

export async function runWithPlugins({ beforeRunContext, run, afterRunContext }) {
  for (const p of plugins) {
    if (p.hooks?.beforeRun) {
      await p.hooks.beforeRun(beforeRunContext);
    }
  }

  const result = await run();

  for (const p of plugins) {
    if (p.hooks?.afterRun) {
      await p.hooks.afterRun(afterRunContext, result);
    }
  }

  if (!result.success) {
    for (const p of plugins) {
      if (p.hooks?.onFailure) {
        await p.hooks.onFailure(afterRunContext, result);
      }
    }
  }

  return result;
}
