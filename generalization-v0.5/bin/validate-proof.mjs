#!/usr/bin/env node
import { validateProof } from '../src/compiler.mjs';

const root = process.argv[2];
if (!root) {
  console.error('Usage: validate-proof <proof-directory>');
  process.exitCode = 2;
} else {
  const result = await validateProof(root);
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
}
