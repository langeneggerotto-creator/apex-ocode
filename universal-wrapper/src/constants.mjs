export const BUILD_ID = 'OCODE_UNIVERSAL_WRAPPER_v0.3_FOUNDER_PROOF_VERTICAL_SLICE';
export const PROOF_VERSION = '0.3.0';
export const SUPPORTED_ADAPTERS = Object.freeze(['expo-typescript']);
export const REQUIRED_BEHAVIORS = Object.freeze([
  'dream_entry',
  'draft_persistence',
  'structured_dream_card',
  'dreamer_correction',
  'exactly_one_next_question'
]);
export const TRUTH = Object.freeze({
  generated: 'GENERATED',
  tested: 'TESTED_IN_NODE_BEHAVIOR_HARNESS',
  structurallyValidated: 'STRUCTURALLY_VALIDATED_NOT_BUNDLED',
  untested: 'NOT_RUN_ON_DEVICE',
  blocked: 'PRODUCTION_DEPLOYMENT_OUT_OF_SCOPE'
});
