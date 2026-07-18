export function createSemanticContract(envelope) {
  return {
    contract_version: '0.3',
    contract_type: 'platform_neutral_interaction_contract',
    intent_id: envelope.intent_id,
    module: {
      id: 'dream_intake',
      title: 'Dream Intake',
      purpose: 'Capture a dream, preserve the original meaning, let the dreamer correct the interpretation, and reduce complexity to one next question.'
    },
    actors: [{ id: 'dreamer', authority: ['enter', 'review', 'correct', 'save', 'continue_or_stop'] }],
    inputs: [
      { id: 'dream_text', type: 'multiline_text', required: true, owner: 'dreamer' },
      { id: 'correction_text', type: 'multiline_text', required: false, owner: 'dreamer' }
    ],
    state: [
      { id: 'draft', persistence: 'local_key_value', retention: 'until_cleared_by_dreamer' },
      { id: 'dream_card', persistence: 'session_and_local_key_value', editable: true },
      { id: 'next_question', cardinality: { minimum: 0, maximum: 1 } }
    ],
    behaviors: [
      { id: 'dream_entry', trigger: 'dreamer_changes_dream_text', result: 'draft_is_available_for_save' },
      { id: 'draft_persistence', trigger: 'dreamer_saves', result: 'draft_can_be_restored' },
      { id: 'structured_dream_card', trigger: 'dreamer_requests_review', result: 'structured_card_is_created_without_external_claims' },
      { id: 'dreamer_correction', trigger: 'dreamer_submits_correction', result: 'card_reflects_correction_and_preserves_revision_history' },
      { id: 'exactly_one_next_question', trigger: 'card_is_available', result: 'zero_or_one_question_is_visible_never_more_than_one' }
    ],
    dream_card_fields: ['title', 'original_dream', 'interpreted_outcome', 'success_signal', 'constraints', 'revision_history'],
    validation: [
      { rule: 'non_empty_dream', failure: 'show_actionable_error' },
      { rule: 'dreamer_retains_edit_authority', failure: 'do_not_promote_interpretation' },
      { rule: 'one_question_maximum', failure: 'block_output_and_repair' }
    ],
    evidence: {
      required: ['behavior_tests', 'source_structure_validation', 'semantic_round_trip_comparison', 'handoff_record'],
      truth_labels: ['generated', 'tested', 'structurally_validated', 'not_run_on_device', 'out_of_scope']
    },
    non_goals: ['production_authentication', 'remote_backend', 'payments', 'live_model_calls', 'store_release', 'multi_screen_navigation']
  };
}

export function assertPlatformNeutral(contract) {
  const serialized = JSON.stringify(contract).toLowerCase();
  const forbidden = ['expo', 'typescript', 'react native', 'react-native', 'swift', 'kotlin', 'flutter'];
  const found = forbidden.filter((term) => serialized.includes(term));
  if (found.length) throw new Error(`Semantic contract is not platform-neutral: ${found.join(', ')}`);
  return true;
}
