export function applyEnv({ baseEnv = {}, variables = {}, secrets = {} }) {
  const maskedSecrets = Object.keys(secrets).reduce((acc, key) => {
    acc[key] = '***';
    return acc;
  }, {});

  return {
    runtimeEnv: {
      ...baseEnv,
      ...variables,
      ...secrets
    },
    maskedView: {
      ...baseEnv,
      ...variables,
      ...maskedSecrets
    }
  };
}

export function redactOutput(output, secrets = {}) {
  let redacted = output;
  for (const val of Object.values(secrets)) {
    if (!val) continue;
    const safe = String(val).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    redacted = redacted.replace(new RegExp(safe, 'g'), '***');
  }
  return redacted;
}
