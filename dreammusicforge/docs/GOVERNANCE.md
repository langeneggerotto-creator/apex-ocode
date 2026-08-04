# DreamMusicForge Governance

## Authority Model

OCode governs repository scope, commands, reversibility, evidence, and release promotion. Coding agents implement only within an approved Delegation Contract.

## Required Delegation Fields

- task ID
- repository and branch
- objective
- allowed and prohibited paths
- allowed commands
- authority level
- reversibility and rollback
- required tests
- evidence requirements
- budget
- stop and escalation conditions

## Promotion States

- experimental
- provisional
- canonical
- quarantined
- deprecated
- rejected

## Promotion Gate

A change may become canonical only when:

1. scope and authority were valid;
2. required tests passed;
3. constitutional invariants remain intact;
4. lineage is complete;
5. evidence supports the claim;
6. known gaps are recorded;
7. rollback remains available;
8. the change is reconstructable by a memoryless system;
9. no unrelated behavior changed silently;
10. human approval is obtained when required.

## Fail-Closed Conditions

Stop when required input, authority, evidence, references, rollback, or verification is unavailable; when an irreversible operation is not approved; or when results contradict the canonical state without an explicit reconciliation process.
