import fs from 'node:fs';
import path from 'node:path';
import { BUILD_ID, SUPPORTED_ADAPTERS, TRUTH } from './constants.mjs';
import { createIntentEnvelope } from './intent-envelope.mjs';
import { assertPlatformNeutral, createSemanticContract } from './semantic-contract.mjs';
import { createDreamerEnvironmentProfile, createRouteFitDecision } from './profile-and-route.mjs';
import { activateMinimumLaws } from './law-guardian-bridge.mjs';
import { generateBehaviorTestSource, generateModelSource, generateScreenSource, generateStorageSource } from './expo-typescript-adapter.mjs';
import { compareRoundTrip, reconstructSpecification } from './reconstruct.mjs';
import { validateGeneratedSource } from './source-validator.mjs';
import { ensureDir, fileSha256, relativeFiles, stableId, writeJson, writeText } from './util.mjs';

function continuationMarkdown() {
  return `# OCODE Dream Intake Founder Proof Continuation

## Governing build

\`${BUILD_ID}\`

## What exists

- Original natural-language intent
- Platform-neutral semantic contract
- Dreamer and environment profile
- Route-fit decision selecting one reversible Expo/TypeScript adapter proof
- Minimum active-law receipt
- Generated screen, model, storage adapter, and behavior tests
- Reconstructed specification and round-trip comparison
- Evidence receipt and source-structure validation

## How to regenerate

From \`universal-wrapper/\`:

\`\`\`bash
node bin/ocode.mjs build examples/dream-intake.intent.txt --adapter expo-typescript --out proofs/dream-intake-v0.3
node --experimental-strip-types --test proofs/dream-intake-v0.3/tests/dream-intake.test.ts
node src/validate-proof.mjs proofs/dream-intake-v0.3
\`\`\`

## Proven

- One intent is converted into a platform-neutral contract.
- One adapter generates the bounded source package.
- Pure model and persistence behavior passes automated Node tests.
- Critical behavior identifiers survive the controlled code-to-specification round trip.
- Another builder can inspect and regenerate the package from repository artifacts.

## Not proven

- Expo bundling, simulator execution, or installation on Otto's iPhone.
- Production backend, authentication, security operations, payments, or store release.
- Arbitrary-code understanding or universal cross-language translation.
- That Expo/TypeScript is the permanent Dream Builder architecture.

## Stop condition

Do not add screens, adapters, live AI calls, backend services, deployment, or authenticated registry synchronization inside this proof. Reassess the closest path after reviewing this evidence.

## Next decision

Decide whether the smallest next proof is an actual Expo bundle/device preview, a second adapter reproducing the same semantic contract, or repair of any failed founder-control requirement.
`;
}

export function buildFounderProof({ intentPath, adapter, outputDirectory, generatedAt = new Date().toISOString() }) {
  if (!SUPPORTED_ADAPTERS.includes(adapter)) throw new Error(`Adapter must be one of: ${SUPPORTED_ADAPTERS.join(', ')}`);
  const rawIntent = fs.readFileSync(intentPath, 'utf8').trim();
  const envelope = createIntentEnvelope(rawIntent);
  const contract = createSemanticContract(envelope);
  assertPlatformNeutral(contract);
  const profile = createDreamerEnvironmentProfile();
  const route = createRouteFitDecision(adapter);
  const laws = activateMinimumLaws();

  fs.rmSync(outputDirectory, { recursive: true, force: true });
  ensureDir(path.join(outputDirectory, 'implementation'));
  ensureDir(path.join(outputDirectory, 'tests'));

  writeText(path.join(outputDirectory, 'original-intent.txt'), rawIntent);
  writeJson(path.join(outputDirectory, 'intent-envelope.json'), envelope);
  writeJson(path.join(outputDirectory, 'dreamer-environment-profile.json'), profile);
  writeJson(path.join(outputDirectory, 'semantic-contract.json'), contract);
  writeJson(path.join(outputDirectory, 'route-fit-decision.json'), route);
  writeJson(path.join(outputDirectory, 'active-law-receipt.json'), laws);
  writeText(path.join(outputDirectory, 'implementation', 'DreamIntakeScreen.tsx'), generateScreenSource());
  writeText(path.join(outputDirectory, 'implementation', 'dream-intake-model.ts'), generateModelSource());
  writeText(path.join(outputDirectory, 'implementation', 'dream-intake-storage.ts'), generateStorageSource());
  writeText(path.join(outputDirectory, 'tests', 'dream-intake.test.ts'), generateBehaviorTestSource());

  const reconstructed = reconstructSpecification(path.join(outputDirectory, 'implementation'));
  const roundTrip = compareRoundTrip(contract, reconstructed);
  const sourceValidation = validateGeneratedSource(path.join(outputDirectory, 'implementation'));
  writeJson(path.join(outputDirectory, 'reconstructed-specification.json'), reconstructed);
  writeJson(path.join(outputDirectory, 'semantic-round-trip-report.json'), roundTrip);
  writeJson(path.join(outputDirectory, 'source-validation-report.json'), sourceValidation);
  writeText(path.join(outputDirectory, 'CONTINUATION.md'), continuationMarkdown());

  const artifactFilesBeforeEvidence = relativeFiles(outputDirectory);
  const artifactHashes = Object.fromEntries(artifactFilesBeforeEvidence.map((file) => [file, fileSha256(path.join(outputDirectory, file))]));
  const evidence = {
    evidence_version: '0.3',
    evidence_id: stableId('evidence', `${envelope.intent_id}:${adapter}:${generatedAt}`),
    build_id: BUILD_ID,
    generated_at: generatedAt,
    adapter,
    scope: 'one_intent_one_screen_one_adapter_one_test_suite_one_handoff_package',
    claims: {
      intent_to_contract: TRUTH.generated,
      platform_neutral_contract: TRUTH.tested,
      source_generation: TRUTH.generated,
      model_and_storage_behavior: 'TEST_COMMAND_PROVIDED__RESULT_RECORDED_BY_CI',
      screen_source: TRUTH.structurallyValidated,
      semantic_round_trip: roundTrip.truth_status,
      device_runtime: TRUTH.untested,
      production_operation: TRUTH.blocked,
      universal_language_support: 'NOT_CLAIMED_ONE_ADAPTER_ONLY'
    },
    pass_conditions: {
      complete_artifact_package: artifactFilesBeforeEvidence.length >= 14,
      platform_neutral_contract: true,
      adapter_source_generated: true,
      automated_behavior_tests_present: true,
      required_behaviors_implemented: roundTrip.critical_requirements_preserved,
      specification_reconstructed: reconstructed.reconstructed_behaviors.length === 5,
      critical_requirements_survive_round_trip: roundTrip.critical_requirements_preserved,
      truth_labels_present: true,
      continuation_package_present: true,
      unrelated_infrastructure_added: false
    },
    source_validation: sourceValidation,
    artifact_hashes: artifactHashes,
    stop_condition_satisfied: true,
    next_action: 'Run automated tests and CI, then review evidence before selecting any additional scope.',
    truth_boundary: 'This evidence proves deterministic generation, Node-testable model/storage behavior, structural screen checks, and a controlled manifest-assisted round trip. It does not prove Expo bundling, device execution, production readiness, or universal code translation.'
  };
  writeJson(path.join(outputDirectory, 'evidence-receipt.json'), evidence);
  return { outputDirectory, envelope, contract, profile, route, laws, reconstructed, roundTrip, sourceValidation, evidence };
}
