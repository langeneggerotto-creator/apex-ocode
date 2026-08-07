# DreamMusicForge Render Intake & Verification v0.1

This kernel is the evidence gate between provider rendering and canonical film state.

## Canonical rule

Renderer output is evidence-bearing candidate media. It never becomes canonical merely because it rendered successfully. Acceptance requires every required gate to be resolved, and any failed critical metric causes rejection.

## Inputs

- a provider execution package
- an imported render candidate bound to that package
- measured or reviewed metric results

## Outputs

- ACCEPT
- REJECT
- REVIEW
- critical failures
- unresolved required gates
- evidence-bearing metric records

## v0.1 deterministic checks

- package binding
- media validity
- duration tolerance
- required acceptance-gate coverage
- fail-closed critical-gate handling
- unresolved-gate review routing

Creative measurements such as identity, costume, world, semantic fidelity, camera intent, continuity, and lip sync enter through typed `MetricResult` records. This release does not pretend to measure those automatically yet.

## Truth boundary

A high average score cannot override a failed critical invariant. Missing required evidence cannot be treated as a pass.

## Known gaps

- no FFmpeg/OpenCV media probe yet
- no automatic face/identity measurement
- no frame-boundary continuity measurement
- no lip-sync measurement
- no evidence-ledger persistence
- no repair-plan compiler
- tests are committed but not claimed as executed in this connector-only increment
