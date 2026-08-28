# DreamMusicForge Continuity Simulation — 2026-08-28

Status: EVIDENCE-BOUNDED LOCAL SIMULATION / CANON INPUT

Scope: reference-video analysis, boundary-transition simulation, perceptual masking, ghosting control, transition timing, and local three-clip assembly.

## 1. Purpose

Improve the DreamMusicForge / APEX Movie Forge process for stitching independently generated video segments so the viewer experiences a seamless cinematic flow comparable to professionally designed hidden transitions.

The attached reference video was treated as the perceptual benchmark. The three previously generated ~15-second Kling-oriented clips were used as the local test sequence.

## 2. Reference-video finding

The reference demonstrates that seamless perceived continuity is not equivalent to minimizing adjacent-frame pixel difference.

Several strong transition moments in the reference contain large frame-to-frame visual changes, yet they remain perceptually coherent because the handoff occurs while continuity-sensitive landmarks are suppressed by one or more of:

- foreground matter filling the frame;
- water/texture filling the frame;
- feather/fabric-like foreground coverage;
- strong motion blur or defocus;
- motivated rapid camera movement;
- temporary loss of stable spatial landmarks.

Measured local transition peaks in the reference could reach roughly 4–10x the neighboring natural frame-change median while still functioning perceptually. Therefore raw frame-difference metrics cannot be the sole verifier.

## 3. Perceptual Masking principle

Add a Perceptual Masking score to every Boundary Contract.

At minimum evaluate:

- frame coverage / occlusion percentage;
- stable-landmark visibility;
- motion-vector direction and speed continuity;
- motion blur / defocus;
- texture fill;
- eye-trace continuity;
- exposure / color continuity;
- character state at reveal;
- camera trajectory at reveal;
- ghosting / double-image risk;
- audio continuity.

A boundary may tolerate a relatively large underlying state reset if the reset occurs inside a sufficiently strong perceptual safe zone and the reveal after the safe zone is coherent.

## 4. Simulation volume

Two simulation stages were executed locally.

### Method-family trials

16 transition methods were tested on each of the two boundaries, for 32 method-boundary trials. Families included:

- hard cut;
- 2/4/6/8/10-frame linear bridges;
- 4/6/8/10-frame optical-flow bridges;
- flow + color matching;
- flow + color matching + zoom variants.

### Parameter-grid trials

A broader parameter search then evaluated:

- Boundary 1 (closed door): 400 parameterized candidates;
- Boundary 2 (foreground person): 2,160 parameterized candidates.

Total parameter-grid trials: 2,560.

The grid varied boundary frame selection, bridge duration, blur, and zoom-related masking parameters.

These are local simulation/search trials, not provider generations.

## 5. Boundary 1 — closed door

Archetype: static near-full-frame occlusion.

Baseline local stitch peak frame difference at the measured boundary was approximately 3.55 at the analysis resolution.

Longer static overlaps substantially reduced the visible step. A 10–12-frame overlap at 30 fps (~0.33–0.40 seconds) was consistently favorable because:

- the frame is almost completely covered;
- meaningful character motion is not visible;
- the door geometry can converge gradually;
- exposure and illumination differences can settle without producing double moving subjects.

A rendered overlap variant reduced the measured visual peak to approximately 1.31, with a targeted local version around 1.27.

### Rule

For STATIC_FULL_COVER boundaries, prefer roughly 10–12 frames at 30 fps unless visual inspection indicates a shorter handoff is cleaner.

## 6. Boundary 2 — foreground person crossing lens

Archetype: dynamic foreground occluder.

The baseline stitch had a measured local visual peak of approximately 14.11 at the analysis resolution.

A long ~0.4–0.5 second generic dissolve reduced the raw peak to approximately 7.81, but visual inspection showed the tradeoff: the lower metric was partially achieved by prolonged double-image / background ghosting.

A targeted simulation instead aligned the foreground crossing trajectory across the tail of clip 2 and head of clip 3, then concentrated the actual handoff into approximately five frames at maximum foreground coverage.

This produced a somewhat higher raw peak than the longest dissolve, but reduced prolonged ghosting and looked closer to the reference-video technique: establish the foreground movement, hide the state reset at maximum coverage, then reveal the new environment only after the handoff.

### Rule

For DYNAMIC_FOREGROUND_OCCLUDER boundaries:

1. align the entire occluder trajectory, not merely two endpoint frames;
2. make entry side, direction and apparent speed agree;
3. reach maximum coverage before the state reset;
4. perform the actual cross-generation handoff in roughly 3–5 frames at maximum coverage;
5. avoid long dissolves that create double bodies or double backgrounds;
6. reveal the new world only after the handoff.

The exact duration remains evidence-driven, not a universal constant.

## 7. Ghosting penalty

The simulation exposed a failure mode in metric-only optimization:

A longer cross-dissolve can score better on adjacent-frame difference while looking worse because two bodies, two environments, or two edge structures coexist visibly.

Therefore the verifier must include a GHOSTING_PENALTY.

A transition cannot be promoted solely because it reduces pixel/frame-difference metrics.

## 8. Boundary-specific timing

Do not use one global transition duration.

Recommended starting ranges from this experiment:

- STATIC_FULL_COVER / closed door: ~10–12 frames at 30 fps;
- DYNAMIC_FOREGROUND_OCCLUDER: establish the motion over a broader window, but concentrate the actual handoff into ~3–5 frames at maximum coverage;
- TEXTURE_FILL / water / smoke / feather / fabric: reference-calibrated safe-zone target roughly ~0.3–0.5 seconds, subject to playback verification;
- WHIP / RAPID_CAMERA_MOVE: cut or bridge at peak motion blur and directional continuity, with stable landmarks suppressed.

These are initialization priors for search, not guaranteed optimal values.

## 9. New transition compiler loop

For every boundary:

DETECT ARCHETYPE
→ FIND MAXIMUM PERCEPTUAL SAFE ZONE
→ ALIGN TRANSITION-OBJECT TRAJECTORY / PHASE
→ SUPPRESS STABLE LANDMARKS
→ SELECT ARCHETYPE-SPECIFIC OVERLAP
→ HAND OFF AT MAXIMUM COVERAGE / BLUR
→ REVEAL NEXT WORLD
→ VERIFY NORMAL PLAYBACK
→ VERIFY FRAME-BY-FRAME
→ SCORE GHOSTING + EYE TRACE + MOTION + AUDIO
→ REPAIR ONLY THE FAILED BOUNDARY

## 10. Audio finding

Local loudness normalization and audio crossfading reduced the second-boundary level jump substantially, but did not solve the first boundary because one source segment was nearly silent.

This reinforces the existing canon:

**Provider clip audio must not define long-form continuity.**

Production should use one continuous master audio timeline for music, dialogue, ambience, Foley and designed transitions. Provider audio is supplemental evidence/material, not the authoritative timeline.

## 11. Best local artifact from this iteration

A new local artifact was rendered:

`seamless_transition_simulation_v2.mp4`

Local construction:

- static door boundary: 12-frame overlap;
- dynamic foreground-person boundary: trajectory-aligned targeted 5-frame handoff;
- H.264 video at 512x910 / 30 fps;
- AAC audio assembled with normalization/crossfades as a best-effort prototype.

The artifact verifies only the local editing/stitching process. It does not prove:

- live Kling generation;
- perfect identity propagation;
- perfect physical spatial continuity;
- perfect audio continuity;
- final delivery quality;
- final cinematic success.

## 12. Updated governing conclusion

The target is not mathematically smallest boundary difference.

The target is:

**the least perceptible, most cinematically motivated boundary that preserves emotion, story, rhythm, eye trace, motion intent and causal continuity.**

In practice, the best seamless transition often deliberately removes the audience's ability to inspect the state reset for a short interval, then reveals a coherent next state.

This document supplements `CONTINUOUS_VIDEO_CANON.md` and should be incorporated into future Boundary Contract, verifier, and transition-compiler implementations.