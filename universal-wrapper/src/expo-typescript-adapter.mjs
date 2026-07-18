import { REQUIRED_BEHAVIORS } from './constants.mjs';

function manifest(kind, capabilities) {
  return `/* OCODE-MANIFEST-BEGIN\n${JSON.stringify({ kind, capabilities }, null, 2)}\nOCODE-MANIFEST-END */`;
}

export function generateModelSource() {
  return `${manifest('model', ['structured_dream_card', 'dreamer_correction', 'exactly_one_next_question'])}
export interface DreamRevision {
  correction: string;
  appliedAt: string;
}

export interface DreamCard {
  title: string;
  originalDream: string;
  interpretedOutcome: string;
  successSignal: string;
  constraints: string[];
  revisionHistory: DreamRevision[];
}

export function normalizeDream(value: string): string {
  return value.trim().replace(/\\s+/g, ' ');
}

export function createDreamCard(rawDream: string): DreamCard {
  const dream = normalizeDream(rawDream);
  if (!dream) throw new Error('Please enter a dream before creating the Dream Card.');
  const words = dream.replace(/[.!?]+$/g, '').split(' ');
  const title = words.slice(0, 7).join(' ');
  return {
    title: title.length < dream.length ? \`${title}…\` : title,
    originalDream: dream,
    interpretedOutcome: dream,
    successSignal: 'The dreamer confirms that this interpretation feels accurate.',
    constraints: ['No unsupported assumptions have been added.'],
    revisionHistory: []
  };
}

export function applyDreamCorrection(card: DreamCard, rawCorrection: string, appliedAt = new Date().toISOString()): DreamCard {
  const correction = normalizeDream(rawCorrection);
  if (!correction) return card;
  return {
    ...card,
    interpretedOutcome: correction,
    revisionHistory: [...card.revisionHistory, { correction, appliedAt }]
  };
}

export function getExactlyOneNextQuestion(card: DreamCard | null): string | null {
  if (!card) return null;
  return 'What would be the clearest real-world sign that this dream has come true?';
}

export const OCODE_REQUIRED_BEHAVIORS = ${JSON.stringify(REQUIRED_BEHAVIORS)} as const;
`;
}

export function generateStorageSource() {
  return `${manifest('storage', ['dream_entry', 'draft_persistence'])}
export interface KeyValueStore {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}

export class MemoryKeyValueStore implements KeyValueStore {
  readonly values = new Map<string, string>();
  async getItem(key: string): Promise<string | null> { return this.values.get(key) ?? null; }
  async setItem(key: string, value: string): Promise<void> { this.values.set(key, value); }
  async removeItem(key: string): Promise<void> { this.values.delete(key); }
}

export class DreamDraftStore {
  static readonly DRAFT_KEY = 'apex.dream-builder.dream-intake.draft.v0.3';
  readonly store: KeyValueStore;
  constructor(store: KeyValueStore) { this.store = store; }
  async saveDraft(dream: string): Promise<void> { await this.store.setItem(DreamDraftStore.DRAFT_KEY, dream); }
  async loadDraft(): Promise<string> { return (await this.store.getItem(DreamDraftStore.DRAFT_KEY)) ?? ''; }
  async clearDraft(): Promise<void> { await this.store.removeItem(DreamDraftStore.DRAFT_KEY); }
}
`;
}

export function generateScreenSource() {
  return `${manifest('screen', REQUIRED_BEHAVIORS)}
import React, { useEffect, useMemo, useState } from 'react';
import { SafeAreaView, ScrollView, StyleSheet, Text, TextInput, Pressable, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { applyDreamCorrection, createDreamCard, getExactlyOneNextQuestion, type DreamCard } from './dream-intake-model';
import { DreamDraftStore } from './dream-intake-storage';

const draftStore = new DreamDraftStore(AsyncStorage);

export default function DreamIntakeScreen() {
  const [dream, setDream] = useState('');
  const [correction, setCorrection] = useState('');
  const [card, setCard] = useState<DreamCard | null>(null);
  const [status, setStatus] = useState('Tell APEX about your dream.');
  const nextQuestion = useMemo(() => getExactlyOneNextQuestion(card), [card]);

  useEffect(() => {
    draftStore.loadDraft().then((saved) => {
      if (saved) {
        setDream(saved);
        setStatus('Your saved draft was restored.');
      }
    });
  }, []);

  async function saveAndReview() {
    try {
      await draftStore.saveDraft(dream);
      setCard(createDreamCard(dream));
      setStatus('Draft saved. Review and correct the Dream Card below.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Unable to create the Dream Card.');
    }
  }

  function applyCorrection() {
    if (!card) return;
    setCard(applyDreamCorrection(card, correction));
    setCorrection('');
    setStatus('Your correction was applied and preserved in the revision history.');
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.eyebrow}>APEX DREAM BUILDER</Text>
        <Text style={styles.heading}>Tell us your dream</Text>
        <Text style={styles.supporting}>Use your own words. You remain in control of the interpretation.</Text>
        <TextInput
          accessibilityLabel="Dream description"
          multiline
          value={dream}
          onChangeText={setDream}
          placeholder="I want to…"
          style={styles.dreamInput}
        />
        <Pressable accessibilityRole="button" onPress={saveAndReview} style={styles.primaryButton}>
          <Text style={styles.primaryButtonText}>Save and review my Dream Card</Text>
        </Pressable>
        <Text accessibilityLiveRegion="polite" style={styles.status}>{status}</Text>

        {card ? (
          <View style={styles.card}>
            <Text style={styles.cardLabel}>DREAM CARD</Text>
            <Text style={styles.cardTitle}>{card.title}</Text>
            <Text style={styles.fieldLabel}>Your original words</Text>
            <Text style={styles.fieldValue}>{card.originalDream}</Text>
            <Text style={styles.fieldLabel}>Current interpretation</Text>
            <Text style={styles.fieldValue}>{card.interpretedOutcome}</Text>
            <Text style={styles.fieldLabel}>Success signal</Text>
            <Text style={styles.fieldValue}>{card.successSignal}</Text>
            <TextInput
              accessibilityLabel="Correct the Dream Card interpretation"
              multiline
              value={correction}
              onChangeText={setCorrection}
              placeholder="Correct anything that does not feel right"
              style={styles.correctionInput}
            />
            <Pressable accessibilityRole="button" onPress={applyCorrection} style={styles.secondaryButton}>
              <Text style={styles.secondaryButtonText}>Apply my correction</Text>
            </Pressable>
            {nextQuestion ? (
              <View style={styles.questionBox}>
                <Text style={styles.questionLabel}>ONE NEXT QUESTION</Text>
                <Text style={styles.question}>{nextQuestion}</Text>
              </View>
            ) : null}
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#F7F5EF' },
  container: { padding: 20, gap: 14 },
  eyebrow: { fontSize: 12, fontWeight: '700', letterSpacing: 1.2 },
  heading: { fontSize: 32, fontWeight: '800' },
  supporting: { fontSize: 16, lineHeight: 23 },
  dreamInput: { minHeight: 150, borderWidth: 1, borderRadius: 16, padding: 16, textAlignVertical: 'top', backgroundColor: '#FFFFFF' },
  primaryButton: { minHeight: 52, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: '#111111', paddingHorizontal: 16 },
  primaryButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700', textAlign: 'center' },
  status: { minHeight: 22, fontSize: 14 },
  card: { borderWidth: 1, borderRadius: 18, padding: 18, gap: 10, backgroundColor: '#FFFFFF' },
  cardLabel: { fontSize: 12, fontWeight: '800', letterSpacing: 1.1 },
  cardTitle: { fontSize: 24, fontWeight: '800' },
  fieldLabel: { marginTop: 6, fontSize: 13, fontWeight: '700' },
  fieldValue: { fontSize: 16, lineHeight: 22 },
  correctionInput: { minHeight: 96, borderWidth: 1, borderRadius: 12, padding: 12, textAlignVertical: 'top' },
  secondaryButton: { minHeight: 48, borderWidth: 1, borderRadius: 12, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 16 },
  secondaryButtonText: { fontSize: 15, fontWeight: '700', textAlign: 'center' },
  questionBox: { marginTop: 8, borderRadius: 14, padding: 14, backgroundColor: '#EFECE3' },
  questionLabel: { fontSize: 11, fontWeight: '800', letterSpacing: 1 },
  question: { marginTop: 6, fontSize: 18, lineHeight: 25, fontWeight: '650' }
});
`;
}

export function generateBehaviorTestSource() {
  return `import test from 'node:test';
import assert from 'node:assert/strict';
import { applyDreamCorrection, createDreamCard, getExactlyOneNextQuestion } from '../implementation/dream-intake-model.ts';
import { DreamDraftStore, MemoryKeyValueStore } from '../implementation/dream-intake-storage.ts';

test('creates a structured Dream Card from dreamer-owned input', () => {
  const card = createDreamCard('I want to build a system that helps people make their dreams come true.');
  assert.equal(card.originalDream, 'I want to build a system that helps people make their dreams come true.');
  assert.equal(card.interpretedOutcome, card.originalDream);
  assert.ok(card.title.length > 0);
  assert.deepEqual(card.revisionHistory, []);
});

test('persists and restores a local draft', async () => {
  const store = new DreamDraftStore(new MemoryKeyValueStore());
  await store.saveDraft('My persistent dream');
  assert.equal(await store.loadDraft(), 'My persistent dream');
  await store.clearDraft();
  assert.equal(await store.loadDraft(), '');
});

test('applies correction without erasing the original dream', () => {
  const original = createDreamCard('I want more freedom.');
  const corrected = applyDreamCorrection(original, 'I want time freedom through a sustainable owner-controlled business.', '2026-07-18T00:00:00.000Z');
  assert.equal(corrected.originalDream, 'I want more freedom.');
  assert.equal(corrected.interpretedOutcome, 'I want time freedom through a sustainable owner-controlled business.');
  assert.equal(corrected.revisionHistory.length, 1);
});

test('returns exactly one next question when a card exists', () => {
  const question = getExactlyOneNextQuestion(createDreamCard('I want to help people.'));
  assert.equal(typeof question, 'string');
  assert.equal((question?.match(/\\?/g) ?? []).length, 1);
  assert.equal(getExactlyOneNextQuestion(null), null);
});
`;
}
