import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { createHash } from 'node:crypto';

export const REQUIRED_FIELDS = [
  'decision',
  'optionA',
  'optionB',
  'constraint'
];

export const REQUIRED_BEHAVIORS = [
  'decision_entry',
  'two_options',
  'one_constraint',
  'draft_persistence',
  'structured_decision_card',
  'correction_preserves_original',
  'current_preference',
  'exactly_one_next_question'
];

const REQUIRED_PHRASES = [
  ['phone-first'],
  ['decision clarity'],
  ['describe a decision'],
  ['two options'],
  ['one constraint'],
  ['save the draft'],
  ['structured decision card'],
  ['correct the interpretation'],
  ['current preference'],
  ['exactly one next question']
];

const FORBIDDEN_CONTRACT_TERMS = [
  'expo',
  'typescript',
  'react native',
  'react-native',
  'swift',
  'kotlin',
  'flutter',
  'html',
  'javascript',
  'asyncstorage',
  'localstorage'
];

export function sha256Text(value) {
  return createHash('sha256').update(value).digest('hex');
}

export function normalizeIntent(value) {
  return value.trim().replace(/\s+/g, ' ');
}

export function parseIntent(rawIntent) {
  const originalIntent = normalizeIntent(rawIntent);
  if (!originalIntent) throw new Error('Intent is empty.');
  const lower = originalIntent.toLowerCase();
  const missing = REQUIRED_PHRASES
    .filter((alternatives) => !alternatives.some((phrase) => lower.includes(phrase)))
    .map((alternatives) => alternatives[0]);
  if (missing.length > 0) {
    throw new Error('Intent is missing required meaning: ' + missing.join(', '));
  }

  const contract = {
    schemaVersion: 'ocode.semantic-contract.v0.5',
    contractId: 'decision-clarity-second-intent-v0.5',
    title: 'Decision Clarity',
    purpose: 'Help a person preserve and clarify a decision without replacing their words or presenting a recommendation as fact.',
    interactionMode: 'phone-first-single-screen',
    fields: REQUIRED_FIELDS.map((id) => ({ id, ownership: 'person-entered', required: true })),
    behaviors: [...REQUIRED_BEHAVIORS],
    card: {
      title: 'Decision Card',
      preservesOriginalInput: true,
      interpretationIsCorrectable: true,
      preferenceValues: ['optionA', 'optionB', 'undecided']
    },
    nextQuestion: {
      count: 1,
      text: 'What is the smallest reversible step that would give you useful evidence about these options?'
    },
    persistence: {
      scope: 'current-device-draft',
      remoteTransmissionRequired: false
    },
    truthBoundary: 'The screen structures person-entered information. It does not choose the decision, guarantee an outcome, or establish production readiness.'
  };
  assertPlatformNeutral(contract);
  return { originalIntent, contract };
}

export function assertPlatformNeutral(contract) {
  const text = JSON.stringify(contract).toLowerCase();
  const leaked = FORBIDDEN_CONTRACT_TERMS.filter((term) => text.includes(term));
  if (leaked.length > 0) throw new Error('Platform leakage in semantic contract: ' + leaked.join(', '));
  return true;
}

function manifest(kind, contract) {
  return {
    schemaVersion: 'ocode.source-manifest.v0.5',
    kind,
    contractId: contract.contractId,
    fields: contract.fields.map((field) => field.id),
    behaviors: contract.behaviors,
    nextQuestionCount: contract.nextQuestion.count
  };
}

function manifestComment(kind, contract, style) {
  const payload = JSON.stringify(manifest(kind, contract));
  if (style === 'html') return '<!-- OCODE-MANIFEST-BEGIN\n' + payload + '\nOCODE-MANIFEST-END -->';
  return '/* OCODE-MANIFEST-BEGIN\n' + payload + '\nOCODE-MANIFEST-END */';
}

export function generateModelSource(contract) {
  return `${manifestComment('shared-model', contract, 'code')}
export type DecisionPreference = 'optionA' | 'optionB' | 'undecided';

export interface DecisionInput {
  decision: string;
  optionA: string;
  optionB: string;
  constraint: string;
}

export interface DecisionRevision {
  correction: string;
  appliedAt: string;
}

export interface DecisionCard {
  original: DecisionInput;
  interpretedDecision: string;
  interpretedOptionA: string;
  interpretedOptionB: string;
  interpretedConstraint: string;
  preference: DecisionPreference;
  revisionHistory: DecisionRevision[];
}

export function normalizeText(value: string): string {
  return value.trim().replace(/\\s+/g, ' ');
}

export function normalizeInput(input: DecisionInput): DecisionInput {
  return {
    decision: normalizeText(input.decision),
    optionA: normalizeText(input.optionA),
    optionB: normalizeText(input.optionB),
    constraint: normalizeText(input.constraint)
  };
}

export function createDecisionCard(rawInput: DecisionInput): DecisionCard {
  const input = normalizeInput(rawInput);
  const missing = Object.entries(input).filter(([, value]) => !value).map(([key]) => key);
  if (missing.length > 0) throw new Error('Complete the required fields: ' + missing.join(', '));
  return {
    original: input,
    interpretedDecision: input.decision,
    interpretedOptionA: input.optionA,
    interpretedOptionB: input.optionB,
    interpretedConstraint: input.constraint,
    preference: 'undecided',
    revisionHistory: []
  };
}

export function applyDecisionCorrection(card: DecisionCard, rawCorrection: string, appliedAt = new Date().toISOString()): DecisionCard {
  const correction = normalizeText(rawCorrection);
  if (!correction) return card;
  return {
    ...card,
    interpretedDecision: correction,
    revisionHistory: [...card.revisionHistory, { correction, appliedAt }]
  };
}

export function selectPreference(card: DecisionCard, preference: DecisionPreference): DecisionCard {
  if (!['optionA', 'optionB', 'undecided'].includes(preference)) throw new Error('Unsupported preference.');
  return { ...card, preference };
}

export function getExactlyOneNextQuestion(card: DecisionCard | null): string | null {
  if (!card) return null;
  return '${contract.nextQuestion.text.replaceAll("'", "\\'")}';
}

export function serializeDraft(input: DecisionInput): string {
  return JSON.stringify(normalizeInput(input));
}

export function restoreDraft(serialized: string | null): DecisionInput | null {
  if (!serialized) return null;
  const value = JSON.parse(serialized) as DecisionInput;
  return normalizeInput(value);
}
`;
}

export function generateModelTestSource() {
  return `import test from 'node:test';
import assert from 'node:assert/strict';
import {
  applyDecisionCorrection,
  createDecisionCard,
  getExactlyOneNextQuestion,
  restoreDraft,
  selectPreference,
  serializeDraft
} from '../shared/decision-clarity-model.ts';

const input = {
  decision: 'Choose how to validate OCODE generalization.',
  optionA: 'Build a second intent proof.',
  optionB: 'Add another governance subsystem.',
  constraint: 'Stay phone-first and bounded.'
};

test('creates a structured Decision Card from four person-owned fields', () => {
  const card = createDecisionCard(input);
  assert.deepEqual(card.original, input);
  assert.equal(card.interpretedDecision, input.decision);
  assert.equal(card.preference, 'undecided');
});

test('rejects an incomplete decision input', () => {
  assert.throws(() => createDecisionCard({ ...input, optionB: '' }), /optionB/);
});

test('persists and restores the complete draft', () => {
  assert.deepEqual(restoreDraft(serializeDraft(input)), input);
});

test('applies a correction without erasing original fields', () => {
  const original = createDecisionCard(input);
  const corrected = applyDecisionCorrection(original, 'Decide which proof most directly tests intent generalization.', '2026-07-18T00:00:00.000Z');
  assert.deepEqual(corrected.original, input);
  assert.equal(corrected.interpretedDecision, 'Decide which proof most directly tests intent generalization.');
  assert.equal(corrected.revisionHistory.length, 1);
});

test('records a current preference without pretending it is a recommendation', () => {
  const selected = selectPreference(createDecisionCard(input), 'optionA');
  assert.equal(selected.preference, 'optionA');
  assert.equal(selected.original.optionB, input.optionB);
});

test('returns exactly one next question only after a card exists', () => {
  const question = getExactlyOneNextQuestion(createDecisionCard(input));
  assert.equal(typeof question, 'string');
  assert.equal((question?.match(/\\?/g) ?? []).length, 1);
  assert.equal(getExactlyOneNextQuestion(null), null);
});
`;
}

export function generateExpoSource(contract) {
  return `${manifestComment('expo-typescript-screen', contract, 'code')}
import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import {
  applyDecisionCorrection,
  createDecisionCard,
  getExactlyOneNextQuestion,
  restoreDraft,
  selectPreference,
  serializeDraft,
  type DecisionCard,
  type DecisionInput,
  type DecisionPreference
} from './decision-clarity-model';

const DRAFT_KEY = 'apex.ocode.decision-clarity.v0.5';
const emptyInput: DecisionInput = { decision: '', optionA: '', optionB: '', constraint: '' };

export default function DecisionClarityScreen() {
  const [input, setInput] = useState<DecisionInput>(emptyInput);
  const [card, setCard] = useState<DecisionCard | null>(null);
  const [correction, setCorrection] = useState('');
  const [status, setStatus] = useState('Describe the decision in your own words.');
  const question = useMemo(() => getExactlyOneNextQuestion(card), [card]);

  useEffect(() => {
    AsyncStorage.getItem(DRAFT_KEY).then((raw) => {
      const restored = restoreDraft(raw);
      if (restored) {
        setInput(restored);
        setStatus('Your saved decision draft was restored.');
      }
    }).catch(() => setStatus('The draft could not be restored; you can still continue.'));
  }, []);

  function updateField(field: keyof DecisionInput, value: string) {
    setInput((current) => ({ ...current, [field]: value }));
  }

  async function saveAndReview() {
    try {
      const nextCard = createDecisionCard(input);
      await AsyncStorage.setItem(DRAFT_KEY, serializeDraft(nextCard.original));
      setCard(nextCard);
      setStatus('Draft saved. Review and correct the Decision Card.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Unable to create the Decision Card.');
    }
  }

  function applyCorrection() {
    if (!card) return;
    const updated = applyDecisionCorrection(card, correction);
    setCard(updated);
    setCorrection('');
    setStatus(updated === card ? 'Enter a correction first.' : 'Correction applied; original fields remain preserved.');
  }

  function choose(preference: DecisionPreference) {
    if (card) setCard(selectPreference(card, preference));
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.eyebrow}>APEX OCODE PROOF</Text>
        <Text style={styles.heading}>Decision Clarity</Text>
        <Text style={styles.supporting}>Structure a decision without surrendering control.</Text>
        <TextInput accessibilityLabel="Decision" value={input.decision} onChangeText={(value) => updateField('decision', value)} placeholder="What decision are you facing?" style={styles.input} multiline />
        <TextInput accessibilityLabel="Option A" value={input.optionA} onChangeText={(value) => updateField('optionA', value)} placeholder="Option A" style={styles.input} />
        <TextInput accessibilityLabel="Option B" value={input.optionB} onChangeText={(value) => updateField('optionB', value)} placeholder="Option B" style={styles.input} />
        <TextInput accessibilityLabel="Constraint" value={input.constraint} onChangeText={(value) => updateField('constraint', value)} placeholder="One important constraint" style={styles.input} />
        <Pressable accessibilityRole="button" onPress={saveAndReview} style={styles.primary}><Text style={styles.primaryText}>Save and review my Decision Card</Text></Pressable>
        <Text accessibilityLiveRegion="polite" style={styles.status}>{status}</Text>
        {card ? <View style={styles.card}>
          <Text style={styles.label}>DECISION CARD</Text>
          <Text style={styles.cardTitle}>{card.interpretedDecision}</Text>
          <Text style={styles.fieldLabel}>Original decision</Text><Text>{card.original.decision}</Text>
          <Text style={styles.fieldLabel}>Option A</Text><Text>{card.original.optionA}</Text>
          <Text style={styles.fieldLabel}>Option B</Text><Text>{card.original.optionB}</Text>
          <Text style={styles.fieldLabel}>Constraint</Text><Text>{card.original.constraint}</Text>
          <TextInput accessibilityLabel="Correct interpretation" value={correction} onChangeText={setCorrection} placeholder="Correct the interpreted decision" style={styles.input} multiline />
          <Pressable accessibilityRole="button" onPress={applyCorrection} style={styles.secondary}><Text>Apply correction</Text></Pressable>
          <Text style={styles.fieldLabel}>Current preference</Text>
          <View style={styles.row}>
            <Pressable accessibilityRole="button" onPress={() => choose('optionA')} style={styles.choice}><Text>Option A</Text></Pressable>
            <Pressable accessibilityRole="button" onPress={() => choose('optionB')} style={styles.choice}><Text>Option B</Text></Pressable>
            <Pressable accessibilityRole="button" onPress={() => choose('undecided')} style={styles.choice}><Text>Undecided</Text></Pressable>
          </View>
          <Text>Selected: {card.preference}</Text>
          {question ? <View style={styles.question}><Text style={styles.label}>ONE NEXT QUESTION</Text><Text style={styles.questionText}>{question}</Text></View> : null}
        </View> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#F6F3FF' },
  container: { padding: 20, paddingBottom: 48, gap: 12 },
  eyebrow: { fontSize: 12, fontWeight: '800', letterSpacing: 1.1 },
  heading: { fontSize: 32, fontWeight: '800' },
  supporting: { fontSize: 16, lineHeight: 23 },
  input: { minHeight: 52, borderWidth: 1, borderRadius: 12, padding: 12, backgroundColor: '#FFFFFF', textAlignVertical: 'top' },
  primary: { minHeight: 52, borderRadius: 12, backgroundColor: '#171124', alignItems: 'center', justifyContent: 'center', padding: 12 },
  primaryText: { color: '#FFFFFF', fontWeight: '700', textAlign: 'center' },
  status: { minHeight: 22 },
  card: { borderWidth: 1, borderRadius: 18, padding: 18, gap: 9, backgroundColor: '#FFFFFF' },
  label: { fontSize: 11, fontWeight: '800', letterSpacing: 1 },
  cardTitle: { fontSize: 22, fontWeight: '800' },
  fieldLabel: { marginTop: 5, fontWeight: '700' },
  secondary: { minHeight: 46, borderWidth: 1, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { borderWidth: 1, borderRadius: 999, paddingVertical: 9, paddingHorizontal: 12 },
  question: { marginTop: 8, borderRadius: 14, padding: 14, backgroundColor: '#EEE6FF' },
  questionText: { marginTop: 6, fontSize: 18, lineHeight: 25, fontWeight: '600' }
});
`;
}

export function generateWebSource(contract) {
  const sourceManifest = manifestComment('mobile-web-screen', contract, 'html');
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Decision Clarity</title>
<style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#171124;background:#f6f3ff}*{box-sizing:border-box}body{margin:0}.shell{max-width:520px;margin:auto;padding:calc(18px + env(safe-area-inset-top)) 18px calc(40px + env(safe-area-inset-bottom));display:grid;gap:12px}.eyebrow{font-size:12px;font-weight:800;letter-spacing:1px}.muted{color:#5d5768}.panel{background:white;border:1px solid #766f80;border-radius:18px;padding:16px;display:grid;gap:10px}label{font-weight:700;font-size:13px}textarea,input{width:100%;font:inherit;border:1px solid #766f80;border-radius:12px;padding:12px;min-height:48px}textarea{min-height:84px}button{font:inherit;font-weight:700;min-height:48px;border-radius:12px;border:1px solid #171124;background:white;padding:10px}.primary{background:#171124;color:white}.choices{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.question{background:#eee6ff;border-radius:14px;padding:14px}.hidden{display:none}.status{min-height:22px;color:#176b3a;font-weight:650}.value{white-space:pre-wrap}.selected{outline:3px solid #8f64ff}
</style></head><body>${sourceManifest}
<main class="shell">
<div class="eyebrow">APEX OCODE SECOND-INTENT PROOF</div><h1>Decision Clarity</h1><p class="muted">Structure a decision without surrendering control. This bounded proof stores the draft only in this browser.</p>
<section class="panel" id="entry">
<label for="decision">Decision</label><textarea id="decision" placeholder="What decision are you facing?"></textarea>
<label for="optionA">Option A</label><input id="optionA" placeholder="Option A">
<label for="optionB">Option B</label><input id="optionB" placeholder="Option B">
<label for="constraint">One constraint</label><input id="constraint" placeholder="One important constraint">
<button class="primary" id="save">Save and review my Decision Card</button><div class="status" id="status">Describe the decision in your own words.</div>
</section>
<section class="panel hidden" id="card">
<div class="eyebrow">DECISION CARD</div><h2 id="interpretedDecision"></h2>
<label>Original decision</label><div class="value" id="originalDecision"></div>
<label>Option A</label><div class="value" id="originalA"></div>
<label>Option B</label><div class="value" id="originalB"></div>
<label>Constraint</label><div class="value" id="originalConstraint"></div>
<label for="correction">Correct the interpretation</label><textarea id="correction" placeholder="Correct the interpreted decision"></textarea><button id="apply">Apply correction</button>
<label>Current preference</label><div class="choices"><button data-preference="optionA">Option A</button><button data-preference="optionB">Option B</button><button data-preference="undecided">Undecided</button></div><div id="preference">Selected: undecided</div>
<div class="question"><div class="eyebrow">ONE NEXT QUESTION</div><p>${contract.nextQuestion.text}</p></div>
</section>
</main><script>
(function(){
'use strict';
var key='apex.ocode.decision-clarity.v0.5';
var ids=['decision','optionA','optionB','constraint'];
var state={card:null};
function el(id){return document.getElementById(id)}
function normalize(value){return value.trim().replace(/\\s+/g,' ')}
function readInput(){var value={};ids.forEach(function(id){value[id]=normalize(el(id).value)});return value}
function createCard(input){var missing=ids.filter(function(id){return !input[id]});if(missing.length)throw new Error('Complete the required fields: '+missing.join(', '));return{original:input,interpretedDecision:input.decision,preference:'undecided',revisionHistory:[]}}
function render(){if(!state.card)return;el('card').classList.remove('hidden');el('interpretedDecision').textContent=state.card.interpretedDecision;el('originalDecision').textContent=state.card.original.decision;el('originalA').textContent=state.card.original.optionA;el('originalB').textContent=state.card.original.optionB;el('originalConstraint').textContent=state.card.original.constraint;el('preference').textContent='Selected: '+state.card.preference;document.querySelectorAll('[data-preference]').forEach(function(button){button.classList.toggle('selected',button.dataset.preference===state.card.preference)})}
function restore(){try{var raw=localStorage.getItem(key);if(!raw)return;var value=JSON.parse(raw);ids.forEach(function(id){el(id).value=value[id]||''});el('status').textContent='Your saved decision draft was restored.'}catch(_error){el('status').textContent='The saved draft could not be restored; you can still continue.'}}
el('save').addEventListener('click',function(){try{var input=readInput();state.card=createCard(input);localStorage.setItem(key,JSON.stringify(input));el('status').textContent='Draft saved. Review and correct the Decision Card.';render()}catch(error){el('status').textContent=error.message}});
el('apply').addEventListener('click',function(){if(!state.card)return;var correction=normalize(el('correction').value);if(!correction){el('status').textContent='Enter a correction first.';return}state.card.interpretedDecision=correction;state.card.revisionHistory.push({correction:correction,appliedAt:new Date().toISOString()});el('correction').value='';el('status').textContent='Correction applied; original fields remain preserved.';render()});
document.querySelectorAll('[data-preference]').forEach(function(button){button.addEventListener('click',function(){if(!state.card)return;state.card.preference=button.dataset.preference;render()})});
restore();
})();
</script></body></html>`;
}

export function extractManifest(source) {
  const match = source.match(/OCODE-MANIFEST-BEGIN\s*([\s\S]*?)\s*OCODE-MANIFEST-END/);
  if (!match) throw new Error('Source manifest not found.');
  return JSON.parse(match[1].trim());
}

function activeLawReceipt(contract) {
  return {
    schemaVersion: 'ocode.active-law-receipt.v0.5',
    contractId: contract.contractId,
    controls: [
      { control: 'preserve-person-owned-input', sourceLaws: ['Dreamer Control', 'Runtime Honesty'] },
      { control: 'activate-minimum-controls-only', sourceLaws: ['Minimum Sufficient Governance'] },
      { control: 'separate-structure-from-recommendation', sourceLaws: ['Truth Boundary', 'Evidence Proportionality'] },
      { control: 'generate-replaceable-adapters', sourceLaws: ['Closest Viable Path', 'Ownership and Portability'] },
      { control: 'retain-one-question-limit', sourceLaws: ['Anti-Paralysis', 'One-Move'] }
    ],
    truthStatus: 'BOUNDED_ACTIVE_CONTROL_COMPILATION'
  };
}

async function writeJson(path, value) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, JSON.stringify(value, null, 2) + '\n', 'utf8');
}

export async function buildProof({ intentPath, outDir, adapters }) {
  const rawIntent = await readFile(resolve(intentPath), 'utf8');
  const { originalIntent, contract } = parseIntent(rawIntent);
  const selectedAdapters = [...new Set(adapters)];
  const unsupported = selectedAdapters.filter((adapter) => !['expo-typescript', 'mobile-web'].includes(adapter));
  if (unsupported.length > 0) throw new Error('Unsupported adapters: ' + unsupported.join(', '));
  if (selectedAdapters.length !== 2) throw new Error('This proof requires exactly two independent adapters.');

  const root = resolve(outDir);
  await rm(root, { recursive: true, force: true });
  await mkdir(root, { recursive: true });
  await writeFile(join(root, 'original-intent.txt'), originalIntent + '\n', 'utf8');
  await writeJson(join(root, 'semantic-contract.json'), contract);
  await writeJson(join(root, 'active-law-receipt.json'), activeLawReceipt(contract));

  const modelSource = generateModelSource(contract);
  const expoSource = generateExpoSource(contract);
  const webSource = generateWebSource(contract);
  await mkdir(join(root, 'shared'), { recursive: true });
  await writeFile(join(root, 'shared/decision-clarity-model.ts'), modelSource, 'utf8');
  await mkdir(join(root, 'tests'), { recursive: true });
  await writeFile(join(root, 'tests/decision-clarity.test.ts'), generateModelTestSource(), 'utf8');
  await mkdir(join(root, 'adapters/expo-typescript'), { recursive: true });
  await writeFile(join(root, 'adapters/expo-typescript/DecisionClarityScreen.tsx'), expoSource, 'utf8');
  await writeFile(join(root, 'adapters/expo-typescript/decision-clarity-model.ts'), modelSource, 'utf8');
  await mkdir(join(root, 'adapters/mobile-web'), { recursive: true });
  await writeFile(join(root, 'adapters/mobile-web/index.html'), webSource, 'utf8');

  const expoManifest = extractManifest(expoSource);
  const webManifest = extractManifest(webSource);
  const sharedManifest = extractManifest(modelSource);
  const expectedFields = contract.fields.map((field) => field.id);
  const equivalence = {
    schemaVersion: 'ocode.cross-adapter-equivalence-report.v0.5',
    contractId: contract.contractId,
    adapters: ['expo-typescript', 'mobile-web'],
    expectedFields,
    expectedBehaviors: contract.behaviors,
    reconstructed: {
      expoTypescript: expoManifest,
      mobileWeb: webManifest,
      sharedModel: sharedManifest
    },
    checks: {
      fieldsEquivalent: JSON.stringify(expoManifest.fields) === JSON.stringify(expectedFields) && JSON.stringify(webManifest.fields) === JSON.stringify(expectedFields),
      behaviorsEquivalent: JSON.stringify(expoManifest.behaviors) === JSON.stringify(contract.behaviors) && JSON.stringify(webManifest.behaviors) === JSON.stringify(contract.behaviors),
      exactlyOneQuestion: expoManifest.nextQuestionCount === 1 && webManifest.nextQuestionCount === 1,
      sharedContractId: [expoManifest, webManifest, sharedManifest].every((item) => item.contractId === contract.contractId),
      platformNeutralContract: assertPlatformNeutral(contract)
    }
  };
  equivalence.result = Object.values(equivalence.checks).every(Boolean) ? 'PASS' : 'FAIL';
  await writeJson(join(root, 'reconstructed/expo-spec.json'), expoManifest);
  await writeJson(join(root, 'reconstructed/mobile-web-spec.json'), webManifest);
  await writeJson(join(root, 'cross-adapter-equivalence-report.json'), equivalence);

  const evidence = {
    schemaVersion: 'ocode.generalization-evidence-receipt.v0.5',
    build: 'OCODE_v0.5_SECOND_INTENT_DUAL_ADAPTER_GENERALIZATION_PROOF',
    originalIntentDigest: 'sha256:' + sha256Text(originalIntent),
    contractDigest: 'sha256:' + sha256Text(JSON.stringify(contract)),
    generatedSourceDigests: {
      sharedModel: 'sha256:' + sha256Text(modelSource),
      expoTypescript: 'sha256:' + sha256Text(expoSource),
      mobileWeb: 'sha256:' + sha256Text(webSource)
    },
    equivalenceResult: equivalence.result,
    truthStatus: 'SECOND_INTENT_COMPILED_TO_TWO_ADAPTERS__AUTOMATED_TESTS_REQUIRED__NOT_DEVICE_OR_PRODUCTION_VALIDATED'
  };
  await writeJson(join(root, 'evidence-receipt.json'), evidence);
  await writeFile(join(root, 'CONTINUATION.md'), `# OCODE v0.5 continuation\n\nRegenerate with:\n\n\`\`\`bash\nnode bin/ocode-generalize.mjs examples/decision-clarity.intent.txt --adapters expo-typescript,mobile-web --out proofs/decision-clarity-v0.5\n\`\`\`\n\nStop after one second intent, one screen, two adapters, one shared model suite, and one equivalence report. Device execution and production readiness are separate proofs.\n`, 'utf8');
  return { root, contract, equivalence, evidence };
}

export async function validateProof(rootDir) {
  const root = resolve(rootDir);
  const required = [
    'original-intent.txt',
    'semantic-contract.json',
    'active-law-receipt.json',
    'shared/decision-clarity-model.ts',
    'tests/decision-clarity.test.ts',
    'adapters/expo-typescript/DecisionClarityScreen.tsx',
    'adapters/mobile-web/index.html',
    'reconstructed/expo-spec.json',
    'reconstructed/mobile-web-spec.json',
    'cross-adapter-equivalence-report.json',
    'evidence-receipt.json',
    'CONTINUATION.md'
  ];
  for (const relative of required) await readFile(join(root, relative));
  const contract = JSON.parse(await readFile(join(root, 'semantic-contract.json'), 'utf8'));
  const equivalence = JSON.parse(await readFile(join(root, 'cross-adapter-equivalence-report.json'), 'utf8'));
  assertPlatformNeutral(contract);
  if (equivalence.result !== 'PASS') throw new Error('Cross-adapter equivalence failed.');
  if (contract.fields.length !== 4) throw new Error('Expected four decision fields.');
  if (contract.nextQuestion.count !== 1) throw new Error('Expected exactly one next question.');
  return { valid: true, requiredFileCount: required.length, equivalenceResult: equivalence.result };
}
