import assert from 'node:assert/strict';
import test from 'node:test';

import {
  applyDreamCorrection,
  createDreamCard,
  getExactlyOneNextQuestion
} from '../src/dream-intake-model.ts';
import { DreamDraftStore, MemoryKeyValueStore } from '../src/dream-intake-storage.ts';

test('creates a Dream Card while preserving the dreamer original words', () => {
  const dream = 'I want to build a system that helps people make their dreams come true.';
  const card = createDreamCard(dream);

  assert.equal(card.originalDream, dream);
  assert.equal(card.interpretedOutcome, dream);
  assert.equal(card.revisionHistory.length, 0);
  assert.ok(card.title.length > 0);
});

test('rejects an empty dream instead of creating an unsupported card', () => {
  assert.throws(() => createDreamCard('   '), /Please enter a dream/);
});

test('persists, restores, and clears a local draft', async () => {
  const store = new DreamDraftStore(new MemoryKeyValueStore());

  await store.saveDraft('My saved dream');
  assert.equal(await store.loadDraft(), 'My saved dream');

  await store.clearDraft();
  assert.equal(await store.loadDraft(), '');
});

test('applies a correction without replacing the original dream', () => {
  const original = createDreamCard('I want more freedom.');
  const corrected = applyDreamCorrection(
    original,
    'I want time freedom through a sustainable owner-controlled business.',
    '2026-07-18T00:00:00.000Z'
  );

  assert.equal(corrected.originalDream, 'I want more freedom.');
  assert.equal(
    corrected.interpretedOutcome,
    'I want time freedom through a sustainable owner-controlled business.'
  );
  assert.equal(corrected.revisionHistory.length, 1);
});

test('returns exactly one next question only after a card exists', () => {
  assert.equal(getExactlyOneNextQuestion(null), null);

  const question = getExactlyOneNextQuestion(createDreamCard('I want to help people.'));
  assert.equal(typeof question, 'string');
  assert.equal((question?.match(/\?/g) ?? []).length, 1);
});
