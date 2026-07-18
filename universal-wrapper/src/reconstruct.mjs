import fs from 'node:fs';
import path from 'node:path';
import { REQUIRED_BEHAVIORS } from './constants.mjs';

function extractManifest(source, file) {
  const match = source.match(/\/\* OCODE-MANIFEST-BEGIN\n([\s\S]*?)\nOCODE-MANIFEST-END \*\//);
  if (!match) throw new Error(`Missing OCODE manifest in ${file}`);
  return JSON.parse(match[1]);
}

export function reconstructSpecification(implementationDirectory) {
  const files = ['DreamIntakeScreen.tsx', 'dream-intake-model.ts', 'dream-intake-storage.ts'];
  const sources = Object.fromEntries(files.map((file) => [file, fs.readFileSync(path.join(implementationDirectory, file), 'utf8')]));
  const manifests = files.map((file) => ({ file, ...extractManifest(sources[file], file) }));
  const capabilities = [...new Set(manifests.flatMap((item) => item.capabilities))].sort();
  const codeSignals = {
    dream_entry: /onChangeText=\{setDream\}/.test(sources['DreamIntakeScreen.tsx']),
    draft_persistence: /saveDraft\(dream\)/.test(sources['DreamIntakeScreen.tsx']) && /loadDraft\(\)/.test(sources['DreamIntakeScreen.tsx']),
    structured_dream_card: /createDreamCard\(dream\)/.test(sources['DreamIntakeScreen.tsx']),
    dreamer_correction: /applyDreamCorrection\(card, correction\)/.test(sources['DreamIntakeScreen.tsx']),
    exactly_one_next_question: (sources['DreamIntakeScreen.tsx'].match(/\{nextQuestion\}/g) ?? []).length === 1
  };
  return {
    reconstruction_version: '0.3',
    method: 'embedded_semantic_manifest_plus_independent_source_signal_checks',
    files_examined: files,
    manifests,
    capabilities,
    code_signals: codeSignals,
    reconstructed_module: 'dream_intake',
    reconstructed_behaviors: REQUIRED_BEHAVIORS.filter((id) => capabilities.includes(id) && codeSignals[id]),
    limitations: [
      'Embedded manifests are generator-produced metadata and are not independent semantic understanding.',
      'Source-signal checks validate the expected generated pattern, not arbitrary TypeScript or every runtime path.',
      'No device execution or production deployment was performed.'
    ]
  };
}

export function compareRoundTrip(contract, reconstructed) {
  const required = contract.behaviors.map((behavior) => behavior.id).sort();
  const reconstructedIds = [...reconstructed.reconstructed_behaviors].sort();
  const missing = required.filter((id) => !reconstructedIds.includes(id));
  const extra = reconstructedIds.filter((id) => !required.includes(id));
  return {
    report_version: '0.3',
    required_behaviors: required,
    reconstructed_behaviors: reconstructedIds,
    missing,
    extra,
    critical_requirements_preserved: missing.length === 0 && extra.length === 0,
    truth_status: missing.length === 0 ? 'ROUND_TRIP_REQUIREMENTS_PRESERVED_IN_BOUNDED_GENERATOR_PROOF' : 'ROUND_TRIP_REPAIR_REQUIRED',
    boundary: 'This comparison validates one known generated pattern. It is not proof of universal code comprehension.'
  };
}
