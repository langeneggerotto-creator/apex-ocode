# APEX Continuity Lab v0.1

A deterministic prototype for reverse-engineering and testing long-form AI-video continuity before spending generation credits.

## What is included

- `reference_profile.json` — evidence-bounded transition map extracted from the supplied reference video.
- `REFERENCE_ANALYSIS.md` — detailed reverse-engineering findings.
- `boundary_contract.schema.json` — provider-neutral Boundary Contract schema.
- `contracts/reference_feather_transition.json` — example contract modeled on a full-frame material/color transition.
- `apex_continuity_simulator.py` — local simulator implementing eight reusable transition mechanisms.
- `test_fault_injection.py` — regression tests proving that identity, footwear, wardrobe, camera scale, screen position and motion-phase drift are rejected.

## Implemented simulator archetypes

1. `nested_portal`
2. `threshold_move`
3. `curtain_wipe`
4. `water_graphic_match`
5. `clapperboard_wipe`
6. `feather_material_wipe`
7. `whip_flash`
8. `match_on_action`

These are mechanisms, not visual presets. A production compiler should map them to the available controls of Kling/Runway/other renderers.

## Production architecture

`CANONICAL MOVIE STATE`
→ `SHOT/SEQUENCE CONTRACT`
→ `BOUNDARY CONTRACT`
→ `PROVIDER COMPILER`
→ `SEGMENT N GENERATION`
→ `EXTRACT ACTUAL END STATE`
→ `LOCK TARGET START STATE`
→ `SEGMENT N+1 GENERATION`
→ `BOUNDARY VERIFIER`
→ PASS or targeted regeneration.

The key change from prompt-only generation is that Segment N+1 does **not** begin from a prose instruction alone. It begins from a serialized state produced by Segment N.

## Hard rule

If identity, footwear, wardrobe, body scale, camera distance or action phase are visibly inconsistent at reveal, the boundary is not seamless. Regenerate the causal segment/boundary. Do not hide the defect with a long dissolve.

## Truth boundary

This prototype verifies the local transition mechanics and deterministic verifier only. It does not prove that any external AI video provider will honor the same state constraints until provider generations are produced and inspected against the contracts.
