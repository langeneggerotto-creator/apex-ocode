#!/usr/bin/env node
import { buildProof } from '../src/compiler.mjs';

function usage() {
  console.error('Usage: ocode-generalize <intent.txt> --adapters expo-typescript,mobile-web --out <proof-directory>');
  process.exitCode = 2;
}

const args = process.argv.slice(2);
if (args.length === 0) {
  usage();
} else {
  const intentPath = args[0];
  const adaptersIndex = args.indexOf('--adapters');
  const outIndex = args.indexOf('--out');
  const adaptersValue = adaptersIndex >= 0 ? args[adaptersIndex + 1] : null;
  const outDir = outIndex >= 0 ? args[outIndex + 1] : null;
  if (!intentPath || !adaptersValue || !outDir) {
    usage();
  } else {
    const result = await buildProof({
      intentPath,
      outDir,
      adapters: adaptersValue.split(',').map((value) => value.trim()).filter(Boolean)
    });
    process.stdout.write(JSON.stringify({
      build: 'OCODE_v0.5_SECOND_INTENT_DUAL_ADAPTER_GENERALIZATION_PROOF',
      proofDirectory: result.root,
      contractId: result.contract.contractId,
      equivalenceResult: result.equivalence.result,
      truthStatus: result.evidence.truthStatus
    }, null, 2) + '\n');
  }
}
