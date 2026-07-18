const LAWS = [
  ['closest_viable_path_to_vision', 'VISION_PATH', 'Require one bounded proof that directly tests OCODE’s universal-wrapper cycle.'],
  ['whole_pathway', 'PATHWAY_FIT', 'Check user, environment, ownership, maintenance, and evidence effects.'],
  ['dreamer_as_infrastructure', 'DREAMER_FIT', 'Use the founder capability and involvement profile.'],
  ['no_premature_architecture', 'PATHWAY_FIT', 'Treat the selected adapter as a reversible proof, not a permanent platform lock.'],
  ['implementation_or_it_did_not_happen', 'EXECUTABLE_PROOF', 'Generate source, tests, reconstruction, evidence, and handoff artifacts.'],
  ['knowledge_is_not_ability', 'DREAMER_FIT', 'Do not claim founder build ability from instructions alone.'],
  ['commitment_follows_evidence', 'EVIDENCE_BOUNDARY', 'Limit commitment until source and behavior evidence exists.'],
  ['dreamer_control', 'OWNERSHIP_CONTROL', 'Preserve edit, stop, correction, repository, and transfer authority.'],
  ['constraint_visibility', 'EVIDENCE_BOUNDARY', 'Label device runtime, deployment, and universality as unproven.'],
  ['anti_paralysis_execution', 'EXECUTABLE_PROOF', 'Produce one working proof rather than another enabling subsystem.'],
  ['runtime_honesty', 'EVIDENCE_BOUNDARY', 'Separate generated source, Node-tested behavior, structural validation, device runtime, and production operation.'],
  ['minimum_sufficient_governance', 'LAW_ECONOMY', 'Compile overlapping laws into a small visible control set.']
];

export function activateMinimumLaws() {
  const groups = new Map();
  for (const [id, group, control] of LAWS) {
    const current = groups.get(group) ?? { id: group, source_laws: [], controls: [] };
    current.source_laws.push(id);
    if (!current.controls.includes(control)) current.controls.push(control);
    groups.set(group, current);
  }
  return {
    receipt_version: '0.3',
    mode: 'PROTOTYPE',
    risk: 'LOW_BOUNDED_REVERSIBLE',
    source_law_count: LAWS.length,
    compiled_control_count: groups.size,
    active_controls: [...groups.values()],
    inactive_by_scope: ['production_security_operations', 'app_store_governance', 'live_customer_data_controls', 'payment_controls', 'multi_agent_authority'],
    decision: 'PROCEED_WITH_CONTROLS',
    human_control: { can_correct: true, can_stop: true, can_reject_adapter: true, constitutional_bypass_allowed: false },
    truth_boundary: 'This is a wrapper-specific minimum law receipt compatible with the Law Guardian design. It does not prove live canonical-registry synchronization or production enforcement.'
  };
}
