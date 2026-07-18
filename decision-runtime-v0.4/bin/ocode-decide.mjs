#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { compileActiveLawSet, selectClosestViablePath, writeEvidenceRecord } from '../src/index.mjs';

function usage() {
  console.error('Usage: ocode-decide <context.json> <candidates.json> [--out receipt.json]');
  process.exitCode = 2;
}

const args = process.argv.slice(2);
if (args.length < 2) {
  usage();
} else {
  const [contextPath, candidatesPath] = args;
  const outIndex = args.indexOf('--out');
  const outPath = outIndex >= 0 ? args[outIndex + 1] : 'evidence/vision-path-selection-receipt.json';
  if (!outPath) {
    usage();
  } else {
    const context = JSON.parse(await readFile(resolve(contextPath), 'utf8'));
    const candidatesPayload = JSON.parse(await readFile(resolve(candidatesPath), 'utf8'));
    const candidates = Array.isArray(candidatesPayload) ? candidatesPayload : candidatesPayload.candidates;
    const activeLawReceipt = compileActiveLawSet(context.laws ?? [], context.policyContext ?? {
      domain: 'software-builder',
      riskLevel: 'low',
      tags: ['reversible-proof']
    });
    const selection = selectClosestViablePath(context, candidates, {
      history: context.buildHistory ?? [],
      stopCondition: context.stopCondition ?? null
    });
    const result = await writeEvidenceRecord(resolve(outPath), {
      evidenceType: 'OCODE_VISION_PATH_SELECTION',
      contextId: context.contextId ?? null,
      selection,
      activeLawReceipt,
      truthStatus: 'DETERMINISTIC_RUNTIME_OUTPUT__NOT_PRODUCTION_OR_DEVICE_VALIDATION'
    });
    process.stdout.write(`${JSON.stringify({
      decision: selection.decision,
      activeRoute: selection.activeRoute?.candidateId ?? null,
      fallbackRoute: selection.fallbackRoute?.candidateId ?? null,
      evidencePath: result.path,
      evidenceDigest: result.fileDigest
    }, null, 2)}\n`);
  }
}
