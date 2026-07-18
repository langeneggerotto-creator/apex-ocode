#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { compilePolicy, LawGuardianError } from './law-guardian.mjs';

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(path.resolve(filePath), 'utf8'));
}

const [lawsPath, contextPath, outputPath] = process.argv.slice(2);
if (!lawsPath || !contextPath) {
  console.error('Usage: node src/cli.mjs <laws.json> <context.json> [receipt.json]');
  process.exit(2);
}

try {
  const laws = readJson(lawsPath);
  const context = readJson(contextPath);
  const receipt = compilePolicy(laws, context);
  const serialized = `${JSON.stringify(receipt, null, 2)}\n`;
  if (outputPath) {
    fs.writeFileSync(path.resolve(outputPath), serialized, 'utf8');
    console.log(`Policy receipt written to ${outputPath}`);
  } else {
    process.stdout.write(serialized);
  }
  process.exitCode = receipt.decision === 'HOLD_FOR_HUMAN_REVIEW' ? 3 : 0;
} catch (error) {
  const payload = {
    error: error instanceof LawGuardianError ? error.name : 'UnhandledError',
    message: error.message,
    details: error.details ?? null
  };
  console.error(JSON.stringify(payload, null, 2));
  process.exit(1);
}
