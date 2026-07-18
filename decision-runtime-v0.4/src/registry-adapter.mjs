import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

export function sha256Text(value) {
  return createHash('sha256').update(value).digest('hex');
}

async function readSource(source, options = {}) {
  if (/^https?:\/\//i.test(source)) {
    const headers = { Accept: 'application/json', ...(options.headers ?? {}) };
    if (options.token) headers.Authorization = `Bearer ${options.token}`;
    const response = await fetch(source, { headers });
    if (!response.ok) throw new Error(`Registry fetch failed with HTTP ${response.status}.`);
    return response.text();
  }
  if (source.startsWith('file://')) return readFile(fileURLToPath(source), 'utf8');
  return readFile(source, 'utf8');
}

export async function loadRegistry(source, options = {}) {
  const raw = await readSource(source, options);
  const digest = sha256Text(raw);
  const expectedDigest = options.expectedDigest ?? null;
  let provenanceStatus = 'UNPINNED';
  if (expectedDigest) provenanceStatus = digest === expectedDigest ? 'PINNED_MATCH' : 'DRIFT_DETECTED';
  return {
    source,
    registry: JSON.parse(raw),
    digest: `sha256:${digest}`,
    expectedDigest: expectedDigest ? `sha256:${expectedDigest.replace(/^sha256:/, '')}` : null,
    provenanceStatus,
    fetchedAt: new Date().toISOString(),
    authenticatedRequest: Boolean(options.token || options.headers?.Authorization)
  };
}
