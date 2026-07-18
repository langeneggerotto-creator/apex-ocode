import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { randomUUID, createHash } from 'node:crypto';

function sortValue(value) {
  if (Array.isArray(value)) return value.map(sortValue);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, sortValue(value[key])]));
  }
  return value;
}

export function canonicalJson(value) {
  return `${JSON.stringify(sortValue(value), null, 2)}\n`;
}

export function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

export async function writeEvidenceRecord(path, record) {
  const payload = {
    schemaVersion: record.schemaVersion ?? 'apex.evidence-record.v0.4',
    evidenceId: record.evidenceId ?? randomUUID(),
    writtenAt: record.writtenAt ?? new Date().toISOString(),
    truthStatus: record.truthStatus ?? 'EVIDENCE_RECORDED__CLAIMS_LIMITED_TO_PAYLOAD',
    ...record
  };
  const withoutDigest = canonicalJson(payload);
  const envelope = {
    ...payload,
    recordDigest: `sha256:${sha256(withoutDigest)}`
  };
  const serialized = canonicalJson(envelope);
  await mkdir(dirname(path), { recursive: true });
  const temporaryPath = `${path}.${process.pid}.${Date.now()}.tmp`;
  await writeFile(temporaryPath, serialized, 'utf8');
  await rename(temporaryPath, path);
  return { path, record: envelope, fileDigest: `sha256:${sha256(serialized)}` };
}

export async function readEvidenceRecord(path) {
  return JSON.parse(await readFile(path, 'utf8'));
}

export function verifyEvidenceRecord(record) {
  const { recordDigest, ...withoutDigest } = record;
  const expected = `sha256:${sha256(canonicalJson(withoutDigest))}`;
  return {
    valid: expected === recordDigest,
    expected,
    actual: recordDigest ?? null
  };
}
