#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import { compilePolicy } from './law-guardian.mjs';
import { loadCanonicalRegistryBundle } from './registry-adapter.mjs';
import { buildCoreOsPolicyEvidenceRecord } from './evidence-record.mjs';
import { assertSchemaValid } from './schema-validator.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const defaults = {
  registry: path.join(root, 'vendor/core-os/apex_core_os_universal_laws_registry_v1.0.json'),
  contract: path.join(root, 'vendor/core-os/core_os_universal_laws_contract.json'),
  manifest: path.join(root, 'vendor/core-os/source-manifest.json'),
  policyMap: path.join(root, 'catalogs/core-os-policy-map-v1.json'),
  schema: path.join(root, 'schemas/core-os-policy-evidence-record-v0.1.schema.json')
};

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.resolve(filePath), 'utf8'));
}

function parseArgs(argv) {
  const positional = [];
  const flags = {};
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (value.startsWith('--')) {
      const key = value.slice(2);
      flags[key] = argv[i + 1];
      i += 1;
    } else positional.push(value);
  }
  return { positional, flags };
}

const { positional, flags } = parseArgs(process.argv.slice(2));
const [contextPath, receiptPath = 'policy-receipt-v0.2.json', evidencePath = 'core-os-policy-evidence-v0.1.json'] = positional;
if (!contextPath) {
  console.error('Usage: node src/registry-cli.mjs <context.json> [policy-receipt.json] [evidence-record.json] [--registry path-or-url --contract path-or-url --manifest path-or-url --policy-map path-or-url --schema path]');
  process.exit(2);
}

try {
  const context = readJson(contextPath);
  const bundle = await loadCanonicalRegistryBundle({
    registry: flags.registry ?? defaults.registry,
    contract: flags.contract ?? defaults.contract,
    manifest: flags.manifest ?? defaults.manifest,
    policyMap: flags['policy-map'] ?? defaults.policyMap
  });
  const receipt = compilePolicy(bundle.laws, context);
  receipt.receiptVersion = '0.2.0';
  receipt.registryProvenance = bundle.provenance;
  receipt.applicableReadinessDimensions = bundle.dimensions;
  receipt.canonicalPromotionGate = bundle.promotionGate;

  const evidence = buildCoreOsPolicyEvidenceRecord({
    receipt,
    bundle,
    subject: context.subject ?? {},
    producer: { commit: process.env.GITHUB_SHA ?? null }
  });
  const schema = readJson(flags.schema ?? defaults.schema);
  assertSchemaValid(evidence, schema, 'Core OS policy evidence record');

  fs.writeFileSync(path.resolve(receiptPath), `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  fs.writeFileSync(path.resolve(evidencePath), `${JSON.stringify(evidence, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify({
    decision: receipt.decision,
    active_controls: receipt.activeControlCount,
    active_law_groups: receipt.activeLawSet.length,
    canonical_laws_loaded: bundle.laws.length,
    registry_sync_status: bundle.provenance.sync_status,
    drift_check_required: bundle.provenance.drift_check_required,
    receipt: receiptPath,
    evidence_record: evidencePath,
    schema_valid: true
  }, null, 2));
  process.exitCode = receipt.decision === 'HOLD_FOR_HUMAN_REVIEW' ? 3 : 0;
} catch (error) {
  console.error(JSON.stringify({
    error: error.name ?? 'UnhandledError',
    message: error.message,
    details: error.details ?? error.validationErrors ?? null
  }, null, 2));
  process.exit(1);
}
