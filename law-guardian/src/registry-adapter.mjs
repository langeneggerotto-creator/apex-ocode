import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';

export class RegistryAdapterError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = 'RegistryAdapterError';
    this.details = details;
  }
}

export function sha256(text) {
  return crypto.createHash('sha256').update(text, 'utf8').digest('hex');
}

async function loadText(source, options = {}) {
  if (typeof source !== 'string' || !source.trim()) {
    throw new RegistryAdapterError('A registry source path or URL is required.');
  }

  if (/^https?:\/\//i.test(source)) {
    const headers = { Accept: 'application/vnd.github.raw+json, application/json, text/plain' };
    if (options.token) headers.Authorization = `Bearer ${options.token}`;
    const response = await fetch(source, { headers });
    if (!response.ok) {
      throw new RegistryAdapterError('Unable to fetch registry source.', {
        source,
        status: response.status,
        authenticated: Boolean(options.token)
      });
    }
    const contentType = response.headers.get('content-type') ?? '';
    if (contentType.includes('application/json')) {
      const payload = await response.json();
      if (payload && typeof payload.content === 'string' && payload.encoding === 'base64') {
        return Buffer.from(payload.content.replace(/\n/g, ''), 'base64').toString('utf8');
      }
      return JSON.stringify(payload, null, 2);
    }
    return response.text();
  }

  return fs.readFile(path.resolve(source), 'utf8');
}

async function loadJson(source, options = {}) {
  const text = await loadText(source, options);
  try {
    return { value: JSON.parse(text), text };
  } catch (error) {
    throw new RegistryAdapterError('Registry source is not valid JSON.', {
      source,
      cause: error.message
    });
  }
}

function uniqueSorted(values) {
  return [...new Set(values ?? [])].sort();
}

function assertEqualSet(label, left, right) {
  const a = uniqueSorted(left);
  const b = uniqueSorted(right);
  if (JSON.stringify(a) !== JSON.stringify(b)) {
    throw new RegistryAdapterError(`${label} mismatch between canonical registry and contract.`, {
      registry: a,
      contract: b
    });
  }
}

function validateRegistryShape(registry, contract, policyMap) {
  if (registry.registry_name !== 'APEX Core OS Universal Laws Registry') {
    throw new RegistryAdapterError('Unexpected Core OS registry name.', {
      registry_name: registry.registry_name
    });
  }
  if (String(registry.version) !== String(contract.version)) {
    throw new RegistryAdapterError('Registry and contract versions do not match.', {
      registry_version: registry.version,
      contract_version: contract.version
    });
  }
  if (String(policyMap.canonical_registry_version) !== String(registry.version)) {
    throw new RegistryAdapterError('Runtime policy map targets a different canonical registry version.', {
      map_version: policyMap.canonical_registry_version,
      registry_version: registry.version
    });
  }

  assertEqualSet('Law inventory', registry.laws, contract.laws);
  assertEqualSet('Readiness dimensions', registry.dimensions, contract.dimensions);
  assertEqualSet('Readiness statuses', registry.statuses, contract.statuses);

  const missingMappings = registry.laws.filter((id) => !policyMap.laws?.[id]);
  const extraMappings = Object.keys(policyMap.laws ?? {}).filter((id) => !registry.laws.includes(id));
  if (missingMappings.length || extraMappings.length) {
    throw new RegistryAdapterError('Policy map and canonical law inventory are not one-to-one.', {
      missingMappings,
      extraMappings
    });
  }

  for (const required of ['READY', 'CONSTRAINED', 'BLOCKED', 'UNKNOWN']) {
    if (!registry.statuses.includes(required)) {
      throw new RegistryAdapterError('Canonical readiness status is missing.', { required });
    }
  }
}

function adaptLaw(id, entry, policyMap) {
  const tier = Number.isInteger(entry.tier) ? entry.tier : policyMap.default_tier;
  const constitutional = Boolean(entry.constitutional || tier === 0);
  return {
    id: `CORE_OS:${id}`,
    canonicalId: id,
    title: entry.title ?? id,
    tier,
    constitutional,
    mandatory: entry.mandatory ?? policyMap.default_mandatory ?? true,
    domains: entry.domains ?? ['*'],
    modes: entry.modes ?? ['*'],
    riskLevels: entry.riskLevels ?? ['*'],
    triggers: entry.triggers ?? [],
    failureMode: entry.failureMode,
    protectedValue: entry.protectedValue,
    controls: [entry.control],
    requiredEvidence: entry.requiredEvidence ?? [],
    mergeKey: entry.mergeKey ?? id,
    conflictsWith: entry.conflictsWith ?? [],
    burden: entry.burden ?? 1,
    protection: entry.protection ?? 1,
    source: 'APEX Core OS Universal Laws Registry v1.0',
    rationale: `Derived runtime mapping for canonical law ${id}.`
  };
}

function determineSyncState(manifest, sources, now, maxSnapshotAgeDays) {
  const remote = [sources.registry, sources.contract].some((value) => /^https?:\/\//i.test(value));
  if (remote) {
    return {
      sync_status: sources.token ? 'AUTHENTICATED_FETCH' : 'LIVE_VERIFIED',
      verified_at: now.toISOString(),
      drift_check_required: false
    };
  }

  const captured = new Date(manifest.snapshot_captured_at);
  const validCaptured = !Number.isNaN(captured.valueOf());
  const ageDays = validCaptured ? (now - captured) / 86_400_000 : Number.POSITIVE_INFINITY;
  const stale = ageDays > maxSnapshotAgeDays;
  return {
    sync_status: stale ? 'STALE_SNAPSHOT' : 'PINNED_SNAPSHOT',
    verified_at: validCaptured ? captured.toISOString() : null,
    drift_check_required: true,
    snapshot_age_days: Number.isFinite(ageDays) ? Number(ageDays.toFixed(2)) : null
  };
}

export async function loadCanonicalRegistryBundle(sources, options = {}) {
  const now = options.now ? new Date(options.now) : new Date();
  if (Number.isNaN(now.valueOf())) throw new RegistryAdapterError('Invalid verification date.');
  const token = options.token ?? process.env.CORE_OS_GITHUB_TOKEN ?? null;
  const maxSnapshotAgeDays = options.maxSnapshotAgeDays ?? 30;

  const [registryData, contractData, mapData, manifestData] = await Promise.all([
    loadJson(sources.registry, { token }),
    loadJson(sources.contract, { token }),
    loadJson(sources.policyMap, { token }),
    loadJson(sources.manifest, { token })
  ]);

  const registry = registryData.value;
  const contract = contractData.value;
  const policyMap = mapData.value;
  const manifest = manifestData.value;
  validateRegistryShape(registry, contract, policyMap);

  const sync = determineSyncState(manifest, { ...sources, token }, now, maxSnapshotAgeDays);
  const laws = registry.laws.map((id) => adaptLaw(id, policyMap.laws[id], policyMap));

  return {
    laws,
    dimensions: [...registry.dimensions],
    statuses: [...registry.statuses],
    gapResponses: [...(contract.gap_responses ?? [])],
    mandatoryArtifacts: [...(contract.mandatory_artifacts ?? [])],
    promotionGate: registry.promotion_gate,
    provenance: {
      registry_name: registry.registry_name,
      version: String(registry.version),
      source_repository: manifest.source_repository ?? 'UNSPECIFIED',
      registry_path: manifest.source_paths?.registry ?? String(sources.registry),
      contract_path: manifest.source_paths?.contract ?? String(sources.contract),
      registry_sha256: sha256(registryData.text),
      contract_sha256: sha256(contractData.text),
      source_blob_sha: manifest.source_blob_shas?.registry ?? null,
      source_contract_blob_sha: manifest.source_blob_shas?.contract ?? null,
      policy_map_sha256: sha256(mapData.text),
      ...sync,
      source_truth_status: registry.truth_status,
      runtime_map_truth_status: policyMap.truth_status,
      boundary: manifest.truth_boundary ?? 'Registry provenance could not be fully established.'
    }
  };
}
