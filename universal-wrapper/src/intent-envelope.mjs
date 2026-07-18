import { REQUIRED_BEHAVIORS } from './constants.mjs';
import { stableId } from './util.mjs';

const REQUIRED_PHRASES = [
  ['phone-first', /phone[- ]first/i],
  ['dream entry', /enter a dream/i],
  ['save', /save it/i],
  ['dream card', /dream card/i],
  ['correction', /correct the interpretation/i],
  ['one next question', /exactly one next question/i]
];

export function createIntentEnvelope(rawIntent) {
  const intent = String(rawIntent ?? '').trim();
  if (!intent) throw new Error('Intent must not be empty.');
  const missing = REQUIRED_PHRASES.filter(([, pattern]) => !pattern.test(intent)).map(([label]) => label);
  if (missing.length) throw new Error(`Intent is missing required proof elements: ${missing.join(', ')}`);
  return {
    envelope_version: '0.3',
    intent_id: stableId('intent', intent),
    raw_intent: intent,
    outcome: 'A phone-first Dream Intake experience that preserves the dreamer’s input and control.',
    primary_user: 'dreamer',
    interaction_mode: 'single_mobile_screen',
    required_behaviors: [...REQUIRED_BEHAVIORS],
    constraints: [
      'one_screen_only',
      'one_adapter_only',
      'no_live_customer_data',
      'no_live_ai_api',
      'no_backend',
      'no_app_store_deployment',
      'reversible_repository_proof'
    ],
    success_boundary: 'Generate, test, reconstruct, and hand off one bounded implementation without claiming device or production validation.'
  };
}
