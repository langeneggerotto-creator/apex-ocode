export function createDreamerEnvironmentProfile() {
  return {
    profile_version: '0.3',
    person: 'Otto',
    role: ['founder', 'product_director', 'ai_directed_builder', 'reviewer'],
    primary_device: 'iPhone',
    secondary_device: 'Windows computer',
    desired_involvement: 'Direct outcomes, inspect behavior and evidence, approve changes, retain ownership; routine manual coding is not required.',
    demonstrated_capabilities: ['natural_language_product_direction', 'screen_review', 'requirements_correction', 'GitHub_governance_direction'],
    unknown_or_unproven: ['local_mobile_build_operation', 'device_runtime_debugging', 'app_store_release', 'long_term_mobile_maintenance'],
    required_controls: ['visible_repository', 'source_ownership', 'rollback', 'test_evidence', 'transferability', 'cost_and_dependency_visibility'],
    capacity_boundary: { initial_work_hours: 8, production_commitment_allowed: false }
  };
}

export function createRouteFitDecision(adapter) {
  const candidates = [
    {
      id: 'expo-typescript',
      fit: 'SELECTED_FOR_BOUNDED_PROOF',
      reasons: ['one_codebase_for_ios_and_android_path', 'repository_source_ownership', 'cloud_build_path_exists', 'fast_screen_proof', 'replaceable_adapter'],
      constraints: ['device_build_not_part_of_this_proof', 'actual_store_release_unproven', 'framework_dependency']
    },
    {
      id: 'web-pwa',
      fit: 'DEFER',
      reasons: ['fast_browser_proof'],
      constraints: ['weaker_native_path_evidence_for_current_vision_test']
    },
    {
      id: 'visual-builder',
      fit: 'DEFER',
      reasons: ['lower_manual_code_burden'],
      constraints: ['exportability_and_round_trip_semantics_require_separate_proof']
    }
  ];
  if (adapter !== 'expo-typescript') throw new Error(`Unsupported adapter: ${adapter}`);
  return {
    decision_version: '0.3',
    decision: 'SELECT_EXPO_TYPESCRIPT_FOR_ONE_REVERSIBLE_PROOF',
    architecture_lock_status: 'NOT_LOCKED_BEYOND_THIS_PROOF',
    selected_adapter: adapter,
    candidates,
    maximum_commitment: 'One screen, one adapter, one test suite, no device deployment.',
    stop_condition: 'Stop after source generation, behavior tests, structural validation, reconstruction, evidence receipt, and handoff are complete.',
    reassessment_trigger: 'Re-rank after proof results or earlier if source ownership, testability, or user control fails.'
  };
}
