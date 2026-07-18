import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { useEffect, useMemo, useState } from 'react';
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View
} from 'react-native';

import {
  applyDreamCorrection,
  createDreamCard,
  getExactlyOneNextQuestion,
  type DreamCard
} from './src/dream-intake-model';
import { DreamDraftStore } from './src/dream-intake-storage';

const draftStore = new DreamDraftStore(AsyncStorage);

export default function App() {
  const [dream, setDream] = useState('');
  const [correction, setCorrection] = useState('');
  const [card, setCard] = useState<DreamCard | null>(null);
  const [status, setStatus] = useState('Tell APEX about your dream.');
  const [isBusy, setIsBusy] = useState(false);

  const nextQuestion = useMemo(() => getExactlyOneNextQuestion(card), [card]);

  useEffect(() => {
    let active = true;

    draftStore
      .loadDraft()
      .then((saved) => {
        if (active && saved) {
          setDream(saved);
          setStatus('Your saved draft was restored on this device.');
        }
      })
      .catch(() => {
        if (active) {
          setStatus('The local draft could not be restored. You can still continue.');
        }
      });

    return () => {
      active = false;
    };
  }, []);

  async function saveAndReview() {
    if (isBusy) {
      return;
    }

    setIsBusy(true);
    try {
      const nextCard = createDreamCard(dream);
      await draftStore.saveDraft(nextCard.originalDream);
      setCard(nextCard);
      setStatus('Draft saved. Review and correct the Dream Card below.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Unable to create the Dream Card.');
    } finally {
      setIsBusy(false);
    }
  }

  function applyCorrection() {
    if (!card) {
      return;
    }

    const updatedCard = applyDreamCorrection(card, correction);
    setCard(updatedCard);
    setCorrection('');
    setStatus(
      updatedCard === card
        ? 'Enter a correction before applying it.'
        : 'Your correction was applied without replacing your original words.'
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
        testID="dream-intake-screen"
      >
        <Text style={styles.eyebrow}>APEX DREAM BUILDER</Text>
        <Text style={styles.heading}>Tell us your dream</Text>
        <Text style={styles.supporting}>
          Use your own words. You remain in control of the interpretation.
        </Text>

        <TextInput
          accessibilityLabel="Dream description"
          multiline
          onChangeText={setDream}
          placeholder="I want to…"
          style={styles.dreamInput}
          testID="dream-input"
          value={dream}
        />

        <Pressable
          accessibilityRole="button"
          disabled={isBusy}
          onPress={saveAndReview}
          style={({ pressed }) => [
            styles.primaryButton,
            pressed ? styles.buttonPressed : null,
            isBusy ? styles.buttonDisabled : null
          ]}
          testID="save-review-button"
        >
          <Text style={styles.primaryButtonText}>
            {isBusy ? 'Saving…' : 'Save and review my Dream Card'}
          </Text>
        </Pressable>

        <Text accessibilityLiveRegion="polite" style={styles.status} testID="status-message">
          {status}
        </Text>

        {card ? (
          <View style={styles.card} testID="dream-card">
            <Text style={styles.cardLabel}>DREAM CARD</Text>
            <Text style={styles.cardTitle}>{card.title}</Text>

            <Text style={styles.fieldLabel}>Your original words</Text>
            <Text style={styles.fieldValue} testID="original-dream">
              {card.originalDream}
            </Text>

            <Text style={styles.fieldLabel}>Current interpretation</Text>
            <Text style={styles.fieldValue} testID="interpreted-outcome">
              {card.interpretedOutcome}
            </Text>

            <Text style={styles.fieldLabel}>Success signal</Text>
            <Text style={styles.fieldValue}>{card.successSignal}</Text>

            <TextInput
              accessibilityLabel="Correct the Dream Card interpretation"
              multiline
              onChangeText={setCorrection}
              placeholder="Correct anything that does not feel right"
              style={styles.correctionInput}
              testID="correction-input"
              value={correction}
            />

            <Pressable
              accessibilityRole="button"
              onPress={applyCorrection}
              style={({ pressed }) => [styles.secondaryButton, pressed ? styles.buttonPressed : null]}
              testID="apply-correction-button"
            >
              <Text style={styles.secondaryButtonText}>Apply my correction</Text>
            </Pressable>

            <Text style={styles.revisionText} testID="revision-count">
              Preserved corrections: {card.revisionHistory.length}
            </Text>

            {nextQuestion ? (
              <View style={styles.questionBox} testID="one-next-question">
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
  safeArea: {
    flex: 1,
    backgroundColor: '#F7F5EF'
  },
  container: {
    padding: 20,
    paddingBottom: 48,
    gap: 14
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.2
  },
  heading: {
    fontSize: 32,
    fontWeight: '800'
  },
  supporting: {
    fontSize: 16,
    lineHeight: 23
  },
  dreamInput: {
    minHeight: 150,
    borderWidth: 1,
    borderColor: '#242424',
    borderRadius: 16,
    padding: 16,
    textAlignVertical: 'top',
    backgroundColor: '#FFFFFF',
    fontSize: 17,
    lineHeight: 24
  },
  primaryButton: {
    minHeight: 52,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#111111',
    paddingHorizontal: 16
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    textAlign: 'center'
  },
  secondaryButton: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: '#242424',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16
  },
  secondaryButtonText: {
    fontSize: 15,
    fontWeight: '700',
    textAlign: 'center'
  },
  buttonPressed: {
    opacity: 0.72
  },
  buttonDisabled: {
    opacity: 0.55
  },
  status: {
    minHeight: 22,
    fontSize: 14
  },
  card: {
    borderWidth: 1,
    borderColor: '#242424',
    borderRadius: 18,
    padding: 18,
    gap: 10,
    backgroundColor: '#FFFFFF'
  },
  cardLabel: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1.1
  },
  cardTitle: {
    fontSize: 24,
    fontWeight: '800'
  },
  fieldLabel: {
    marginTop: 6,
    fontSize: 13,
    fontWeight: '700'
  },
  fieldValue: {
    fontSize: 16,
    lineHeight: 22
  },
  correctionInput: {
    minHeight: 96,
    borderWidth: 1,
    borderColor: '#777777',
    borderRadius: 12,
    padding: 12,
    textAlignVertical: 'top',
    fontSize: 16,
    lineHeight: 22
  },
  revisionText: {
    fontSize: 13
  },
  questionBox: {
    marginTop: 8,
    borderRadius: 14,
    padding: 14,
    backgroundColor: '#EFECE3'
  },
  questionLabel: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1
  },
  question: {
    marginTop: 6,
    fontSize: 18,
    lineHeight: 25,
    fontWeight: '600'
  }
});
