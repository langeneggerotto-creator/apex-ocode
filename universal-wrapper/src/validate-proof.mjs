#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { assertPlatformNeutral } from './semantic-contract.mjs';
import { readJson, relativeFiles } from './util.mjs';

export const REQUIRED_FILES = [
  'original-intent.txt',
  'intent-envelope.json',
  'dreamer-environment-profile.json',
  'semantic-contract.json',
  'route-fit-decision.json',
  'active-law-receipt.json',
  'implementation/DreamIntakeScreen.tsx',
  'implementation/dream-intake-model.ts',
  'implementation/dream-intake-storage.ts',
  'tests/dream-intake.test.ts',
  'reconstructed-specification.json',
  'semantic-round-trip-report.json',
  'source-validation-report.json',
  'evidence-receipt.json',
  'CONTINUATION.md'
];

export function validateProof(root) {
  const available = new Set(relativeFiles(root));
  const missing = REQUIRED_FILES.filter((file) => !available.has(file));
  const contract = readJson(path.join(root, 'semantic-contract.json'));
  const roundTrip = readJson(path.join(root, 'semantic-round-trip-report.json'));
  const source = readJson(path.join(root, 'source-validation-report.json'));
  const evidence = readJson(path.join(root, 'evidence-receipt.json'));
  const laws = readJson(path.join(root, 'active-law-receipt.json'));
  assertPlatformNeutral(contract);
  const checks = {
    no_missing_files: missing.length === 0,
    critical_round_trip_preserved: roundTrip.critical_requirements_preserved === true,
    source_structurally_validated: source.passed === true,
    law_economy_compiled: laws.compiled_control_count < laws.source_law_count,
    one_adapter_only: evidence.adapter === 'expo-typescript',
    no_unrelated_infrastructure: evidence.pass_conditions.unrelated_infrastructure_added === false,
    stop_condition_satisfied: evidence.stop_condition_satisfied === true,
    device_runtime_not_overclaimed: evidence.claims.device_runtime === 'NOT_RUN_ON_DEVICE'
  };
  const failed = Object.entries(checks).filter(([, value]) => !value).map(([key]) => key);
  return { validation_version: '0.3', checks, missing, failed, passed: failed.length === 0 };
}

if (process.argv[1] && process.argv[1].endsWith('validate-proof.mjs')) {
  const root = path.resolve(process.argv[2] ?? 'proofs/dream-intake-v0.3');
  if (!fs.existsSync(root)) {
    console.error(JSON.stringify({ passed: false, error: `Proof directory not found: ${root}` }, null, 2));
    process.exit(1);
  }
  const result = validateProof(root);
  console.log(JSON.stringify(result, null, 2));
  if (!result.passed) process.exit(1);
}
