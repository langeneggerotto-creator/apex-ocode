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
  return value.trim().replace(/\s+/g, ' ');
}

export function createDreamCard(rawDream: string): DreamCard {
  const dream = normalizeDream(rawDream);
  if (!dream) {
    throw new Error('Please enter a dream before creating the Dream Card.');
  }

  const titleWords = dream.replace(/[.!?]+$/g, '').split(' ').slice(0, 7);
  const title = titleWords.join(' ');

  return {
    title: title.length < dream.length ? `${title}…` : title,
    originalDream: dream,
    interpretedOutcome: dream,
    successSignal: 'The dreamer confirms that this interpretation feels accurate.',
    constraints: ['No unsupported assumptions have been added.'],
    revisionHistory: []
  };
}

export function applyDreamCorrection(
  card: DreamCard,
  rawCorrection: string,
  appliedAt = new Date().toISOString()
): DreamCard {
  const correction = normalizeDream(rawCorrection);
  if (!correction) {
    return card;
  }

  return {
    ...card,
    interpretedOutcome: correction,
    revisionHistory: [...card.revisionHistory, { correction, appliedAt }]
  };
}

export function getExactlyOneNextQuestion(card: DreamCard | null): string | null {
  if (!card) {
    return null;
  }

  return 'What would be the clearest real-world sign that this dream has come true?';
}
