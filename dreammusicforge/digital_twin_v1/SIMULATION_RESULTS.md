# APEX Digital Twin 30s Continuity Simulation v1

Status: VERIFIED LOCAL DIGITAL-TWIN SIMULATION
Date: 2026-08-28

## Objective

Simulate a 30-second continuous cinematic sequence as three independently rendered 10-second execution windows while preserving one canonical character, camera, motion clock, world-state progression, and uninterrupted audio master.

The test is designed to validate the APEX Continuous Video Workflow principle that renderer segment boundaries must not become viewer-visible cinematic boundaries.

## Architecture

- Segment 1: 0–10 s
- Segment 2: 10–20 s
- Segment 3: 20–30 s
- 30 fps, 540×960
- Same deterministic character identity model across all three windows
- Same dress and footwear geometry across all three windows
- One global gait/motion clock across all windows
- One global camera/screen-position state
- One continuous 30-second audio master
- Environment change at 10 s hidden under a dark full-frame moving panel/door safe zone
- Environment change at 20 s hidden under a continuous full-frame flowing-fabric safe zone

## Verification

Decoded output length: 900 frames.

Normal adjacent-frame motion:

- median adjacent-frame MAE: 1.1319
- 95th percentile adjacent-frame MAE: 2.2851

Boundary around 10 s:

- peak adjacent-frame MAE in ±10-frame window: 2.3596
- mean adjacent-frame MAE in boundary window: 0.6290

Boundary around 20 s:

- peak adjacent-frame MAE in ±10-frame window: 2.5967
- mean adjacent-frame MAE in boundary window: 1.8208

These peaks are close to the ordinary-motion range of the simulation rather than large cut-like outliers.

State continuity across the two execution-window handoffs:

- identity: EXACT_BY_CONSTRUCTION
- wardrobe: EXACT_BY_CONSTRUCTION
- footwear: EXACT_BY_CONSTRUCTION
- audio: SINGLE_CONTINUOUS_MASTER
- subject screen-x delta at both handoffs: 0 px
- subject-scale deltas: ~0.00015
- gait-phase advance is continuous and corresponds to normal one-frame temporal progression rather than a phase reset

## Important refinement

The first version of the 20-second material transition had a peak MAE of about 9.11 because the simulation switched between two material-rendering modes near the handoff. The second pass replaced that with one continuous flowing fabric field whose opacity changes smoothly while the world changes behind it. The boundary peak dropped to about 2.60 while preserving full perceptual masking.

This is an example of simulation-driven continuity refinement.

## Truth boundary

This verifies a deterministic local digital-twin workflow in which three separately rendered execution windows inherit one canonical state and can be assembled without an obvious state reset.

It does not prove that Kling, Runway, Seedance, Veo, Hailuo, or another stochastic generative-video model will preserve the same invariants without further provider-specific controls and verification.

The next provider experiment should use these exact principles: actual terminal-state propagation, locked identity/wardrobe/footwear, continuous motion phase, boundary safe zones, continuous audio, multi-candidate generation, and Continuity Lab rejection of drifted outputs.
