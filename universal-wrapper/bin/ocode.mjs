#!/usr/bin/env node
import path from 'node:path';
import process from 'node:process';
import { buildFounderProof } from '../src/build-proof.mjs';

function usage() {
  console.error('Usage: ocode build <intent-file> --adapter expo-typescript [--out proofs/dream-intake-v0.3]');
}

const args = process.argv.slice(2);
if (args[0] !== 'build' || !args[1]) {
  usage();
  process.exit(2);
}
const valueAfter = (flag, fallback = null) => {
  const index = args.indexOf(flag);
  return index >= 0 ? args[index + 1] : fallback;
};
const adapter = valueAfter('--adapter');
const out = valueAfter('--out', 'proofs/dream-intake-v0.3');
if (!adapter || !out) {
  usage();
  process.exit(2);
}
try {
  const result = buildFounderProof({
    intentPath: path.resolve(args[1]),
    adapter,
    outputDirectory: path.resolve(out)
  });
  console.log(JSON.stringify({
    status: 'FOUNDER_PROOF_GENERATED',
    build: 'OCODE_UNIVERSAL_WRAPPER_v0.3_FOUNDER_PROOF_VERTICAL_SLICE',
    output: result.outputDirectory,
    decision: result.laws.decision,
    round_trip_preserved: result.roundTrip.critical_requirements_preserved,
    source_validation: result.sourceValidation.truth_status,
    truth_boundary: result.evidence.truth_boundary
  }, null, 2));
} catch (error) {
  console.error(JSON.stringify({ status: 'BUILD_FAILED', message: error.message }, null, 2));
  process.exit(1);
}
