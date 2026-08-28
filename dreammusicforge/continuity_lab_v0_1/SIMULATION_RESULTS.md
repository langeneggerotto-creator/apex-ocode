# APEX Continuity Lab v0.1 — Simulation Results

Local deterministic simulation was executed on 2026-08-28.

## Passing archetype simulations

| Archetype | Score | Max masking/coverage | Peak frame MAE | Result |
|---|---:|---:|---:|---|
| Nested frame portal | 98.73 | 1.000 | 6.763 | PASS |
| Threshold / doorway continuity | 99.45 | 0.905 | 2.932 | PASS |
| Curtain full-frame wipe | 99.36 | 1.000 | 3.432 | PASS |
| Water → circular graphic match | 97.65 | 1.000 | 12.508 | PASS |
| Clapperboard full-frame wipe | 98.88 | 1.000 | 5.971 | PASS |
| Feather/material color morph | 96.51 | 1.000 | 18.607 | PASS |
| Whip/flash motion bridge | 97.83 | 0.941 | 11.565 | PASS |
| Match on action | 99.63 | N/A | 1.995 | PASS |

The water/graphic-match simulation initially failed because the masking region reached only ~0.672 coverage. The simulator was changed so the splash becomes a true full-frame safe zone before resolving into circular geometry. The rerun reached 1.000 coverage and passed. This is evidence of simulation-driven refinement, not a claim about external provider output.

## Fault-injection regression

The clean control passed. Every deliberate continuity defect below was rejected:

- identity drift — FAIL;
- footwear drift — FAIL;
- wardrobe drift — FAIL;
- camera/subject-scale drift (+9%) — FAIL;
- screen-position drift (+8% frame width) — FAIL;
- motion-phase drift (+0.26 cycle) — FAIL.

This directly encodes the lesson from the prior stitched experiment: a transition is not seamless merely because the cut is hidden. The revealed state must still satisfy identity, footwear, wardrobe, camera-distance/scale, position and performance continuity.

## Truth boundary

These results verify deterministic local simulator behavior and fault detection only. They do not prove provider compliance, photorealistic identity preservation, or final cinematic quality from Kling, Runway, or any other renderer.
