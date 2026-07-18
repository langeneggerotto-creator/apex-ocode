import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { compilePolicy } from '../src/law-guardian.mjs';
import { loadCanonicalRegistryBundle, RegistryAdapterError } from '../src/registry-adapter.mjs';
import { buildCoreOsPolicyEvidenceRecord } from '../src/evidence-record.mjs';
import { validateAgainstSchema } from '../src/schema-validator.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sources = {
  registry: path.join(root, 'vendor/core-os/apex_core_os_universal_laws_registry_v1.0.json'),
  contract: path.join(root, 'vendor/core-os/core_os_universal_laws_contract.json'),
  manifest: path.join(root, 'vendor/core-os/source-manifest.json'),
  policyMap: path.join(root, 'catalogs/core-os-policy-map-v1.json')
};
const schemaPath = path.join(root, 'schemas/core-os-policy-evidence-record-v0.1.schema.json');

async function loadJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

function prototypeContext() {
  return {
    taskId: 'DREAM-BUILDER-MOBILE-SCREEN-01',
    description: 'Build a reversible two-screen Dream Builder prototype.',
    domain: 'SOFTWARE',
    mode: 'PROTOTYPE',
    riskLevel: 'LOW',
    reversible: true,
    affectedParties: 1,
    evidence: { truth_boundary_recorded: true },
    subject: {
      repository: 'langeneggerotto-creator/oil-projects',
      project: 'Dream Builder',
      module: 'mobile-feasibility',
      artifact: 'two-screen-prototype',
      version: '0.1'
    }
  };
}

test('loads the provenance-pinned canonical registry and all 24 mapped laws', async () => {
  const bundle = await loadCanonicalRegistryBundle(sources, { now: '2026-07-18T00:00:00Z' });
  assert.equal(bundle.laws.length, 24);
  assert.equal(bundle.dimensions.length, 12);
  assert.equal(bundle.provenance.sync_status, 'PINNED_SNAPSHOT');
  assert.equal(bundle.provenance.drift_check_required, true);
  assert.match(bundle.provenance.registry_sha256, /^[a-f0-9]{64}$/);
  assert.match(bundle.provenance.contract_sha256, /^[a-f0-9]{64}$/);
});

test('compiles canonical laws into a reduced active control set', async () => {
  const bundle = await loadCanonicalRegistryBundle(sources, { now: '2026-07-18T00:00:00Z' });
  const receipt = compilePolicy(bundle.laws, prototypeContext());
  assert.equal(receipt.decision, 'PROCEED_WITH_CONTROLS');
  assert.ok(receipt.activeLawSet.length < bundle.laws.length);
  assert.ok(receipt.activeLawSet.some((group) => group.sourceLawIds.includes('CORE_OS:constraint_visibility')));
  assert.ok(receipt.simplificationRecommendations.some((item) => item.action === 'MERGED_DUPLICATE_CONTROLS'));
});

test('produces an Evidence Ledger compatible schema-valid record', async () => {
  const bundle = await loadCanonicalRegistryBundle(sources, { now: '2026-07-18T00:00:00Z' });
  const receipt = compilePolicy(bundle.laws, prototypeContext());
  receipt.receiptVersion = '0.2.0';
  receipt.registryProvenance = bundle.provenance;
  const record = buildCoreOsPolicyEvidenceRecord({ receipt, bundle, subject: prototypeContext().subject });
  const schema = await loadJson(schemaPath);
  const validation = validateAgainstSchema(record, schema);
  assert.equal(validation.valid, true, JSON.stringify(validation.errors));
  assert.equal(record.record_type, 'CORE_OS_POLICY_EVIDENCE');
  assert.equal(record.inherited_law.sync_status, 'PINNED_SNAPSHOT');
  assert.ok(record.unresolved_gaps.includes('CANONICAL_REGISTRY_DRIFT_CHECK_REQUIRED'));
});

test('schema validator rejects a receipt missing a required field', async () => {
  const schema = await loadJson(schemaPath);
  const validation = validateAgainstSchema({ record_type: 'CORE_OS_POLICY_EVIDENCE' }, schema);
  assert.equal(validation.valid, false);
  assert.ok(validation.errors.some((error) => error.path.endsWith('.record_id')));
});

test('registry and contract law drift is blocked', async () => {
  const temp = await fs.mkdtemp(path.join(os.tmpdir(), 'ocode-registry-'));
  const contract = await loadJson(sources.contract);
  contract.laws = contract.laws.slice(1);
  const contractPath = path.join(temp, 'contract.json');
  await fs.writeFile(contractPath, JSON.stringify(contract), 'utf8');
  await assert.rejects(
    loadCanonicalRegistryBundle({ ...sources, contract: contractPath }),
    (error) => error instanceof RegistryAdapterError && /Law inventory mismatch/.test(error.message)
  );
});

test('missing policy mapping is blocked', async () => {
  const temp = await fs.mkdtemp(path.join(os.tmpdir(), 'ocode-map-'));
  const policyMap = await loadJson(sources.policyMap);
  delete policyMap.laws.whole_pathway;
  const mapPath = path.join(temp, 'map.json');
  await fs.writeFile(mapPath, JSON.stringify(policyMap), 'utf8');
  await assert.rejects(
    loadCanonicalRegistryBundle({ ...sources, policyMap: mapPath }),
    (error) => error instanceof RegistryAdapterError && /one-to-one/.test(error.message)
  );
});

test('old pinned snapshots are labeled stale rather than current', async () => {
  const temp = await fs.mkdtemp(path.join(os.tmpdir(), 'ocode-manifest-'));
  const manifest = await loadJson(sources.manifest);
  manifest.snapshot_captured_at = '2020-01-01T00:00:00Z';
  const manifestPath = path.join(temp, 'manifest.json');
  await fs.writeFile(manifestPath, JSON.stringify(manifest), 'utf8');
  const bundle = await loadCanonicalRegistryBundle({ ...sources, manifest: manifestPath }, {
    now: '2026-07-18T00:00:00Z',
    maxSnapshotAgeDays: 30
  });
  assert.equal(bundle.provenance.sync_status, 'STALE_SNAPSHOT');
  assert.equal(bundle.provenance.drift_check_required, true);
});

test('evidence record never claims runtime controls were executed', async () => {
  const bundle = await loadCanonicalRegistryBundle(sources, { now: '2026-07-18T00:00:00Z' });
  const receipt = compilePolicy(bundle.laws, prototypeContext());
  const record = buildCoreOsPolicyEvidenceRecord({ receipt, bundle, subject: prototypeContext().subject });
  assert.equal(record.implementation_status, 'PARTIALLY_IMPLEMENTED');
  assert.match(record.truth_boundary, /does not prove that runtime controls were executed/i);
});
