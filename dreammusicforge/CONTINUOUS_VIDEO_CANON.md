# DreamMusicForge Continuous Video Canon

Status: CANONICAL DESIGN / EVIDENCE-BOUNDED
Date: 2026-08-28
Scope: DreamMusicForge / APEX Movie Forge long-form video continuity, Kling-oriented generation, editorial stitching, audio continuity, verification, and repair.

## 1. Core conclusion

DreamMusicForge must not define long-form continuity as a requirement for a renderer to generate one uninterrupted 45/60/90-second take.

The preferred architecture is one **perceptually continuous cinematic experience** composed from manageable generated segments, with:

1. true continuity when it is achievable and cinematically valuable;
2. concealed continuity when a cut can be hidden more reliably than exact state propagation;
3. motivated scene transitions when the story intentionally changes space or state;
4. ordinary editorial cuts whenever they are superior for emotion, story, rhythm, or clarity.

Continuity is a cinematic tool, not a universal objective.

## 2. Formal continuity classes

### 2.1 TRUE_CONTINUOUS_SPAN

A span may be called true continuous only when the relevant state actually propagates across the boundary:

- same physical space/world state;
- same character identity and appearance state;
- continuous body pose and motion state;
- continuous camera transform and lens state;
- continuous lighting/environment state;
- continuous temporal causality;
- no hidden editorial reset masquerading as physical continuity.

### 2.2 CONCEALED_CONTINUITY_SPAN

A real cut or regenerated segment boundary exists, but the boundary is perceptually hidden using an occlusion or other visual condition that temporarily removes the viewer's ability to inspect continuity-sensitive state.

Examples:

- foreground person passing close to camera;
- door closing across the frame;
- camera moving behind a wall or pillar;
- darkness or blackout;
- whip pan / motion blur;
- smoke, fabric, hair, crowd, vehicle or prop crossing lens;
- lens flare or overexposure;
- object pushed toward lens;
- camera passing behind architecture.

This is a valid filmmaking technique and should be deliberately authored rather than treated as a workaround of last resort.

### 2.3 MOTIVATED_SCENE_TRANSITION

A hidden or visible transition intentionally changes location, spatial state, time, environment, or narrative condition while preserving perceptual and story flow.

A transition must not be mislabeled as true physical continuity when the underlying geography or state has changed.

## 3. Boundary Contract

Every generated segment that participates in a continuity handoff must have an explicit Boundary Contract.

Minimum tracked state:

### Character

- CHARACTER_ID
- FACE_STATE
- HAIR_STATE
- WARDROBE_STATE
- BODY_POSE
- LEFT_FOOT_PHASE
- RIGHT_FOOT_PHASE
- ARM_SWING
- WALK_VELOCITY
- GAZE
- EXPRESSION
- PERFORMANCE_INTENT

### Camera

- CAMERA_POSITION
- CAMERA_ORIENTATION
- CAMERA_HEIGHT
- LENS / FOCAL_BEHAVIOR
- CAMERA_TRAJECTORY
- CAMERA_VELOCITY
- FOCUS_STATE
- DEPTH_OF_FIELD
- EXPOSURE / WHITE_BALANCE intent

### World / space

- WORLD_ID
- SPACE_ID
- SCENE_STATE
- SUBJECT_POSITION_IN_SPACE
- LIGHTING_STATE
- BACKGROUND_GEOMETRY_STATE
- OCCLUDER_STATE
- PORTAL / DOOR / ARCHITECTURAL_STATE

### Boundary device

- BOUNDARY_DEVICE_TYPE
- COVERAGE_TARGET_PERCENT
- MINIMUM_SAFE_COVERAGE_DURATION_FRAMES
- MOTION_DIRECTION
- OCCLUDER_APPEARANCE
- ALLOWED_STATE_CHANGES_DURING_COVERAGE
- REQUIRED_NEXT_SEGMENT_START_STATE

### Audio

- MASTER_AUDIO_TIME
- DIALOGUE_STATE
- MUSIC_STATE
- AMBIENCE_STATE
- SFX_STATE
- FOOTSTEP_PHASE when relevant
- provider-audio harvesting policy

## 4. Continuity safe zone

A transition should deliberately create a **continuity safe zone** when exact renderer-state continuation is unreliable.

Preferred pattern:

1. source segment approaches high frame coverage by an occluder or transition device;
2. coverage rises toward near-total or total visual masking;
3. a short bridge region may be synthesized/interpolated while visibility of continuity-sensitive state is minimal;
4. target segment begins while the same transition device still dominates the frame;
5. coverage recedes and the next scene state becomes visible.

Illustrative target:

- 90% coverage
- 95% coverage
- 100% / near-100% safe zone
- optional 4-8 bridge frames
- 100% / near-100% coverage
- 95% coverage
- target segment reveal

Exact thresholds are implementation parameters, not proof of invisibility. They must be validated visually.

## 5. August 28, 2026 three-clip experiment

Three independently generated approximately 15-second vertical clips were analyzed and stitched into one approximately 44.6-second sequence.

### Boundary A: clip 1 -> clip 2

Transition device: closed door.

Observed result:

- strong concealment concept;
- near-matching closed-door frames allowed redundant overlap to be trimmed;
- small geometric/lighting differences remained visible under scrutiny;
- measured adjacent-boundary grayscale mean absolute difference was approximately 6.4 levels versus roughly 3.0 for an ordinary adjacent frame in the stitched sequence.

Interpretation:

The transition concept is strong, but a few matching/bridge frames or stronger geometry locking could improve invisibility.

### Boundary B: clip 2 -> clip 3

Transition device: foreground person passing close to the lens.

Observed result:

- the occluder successfully hid a much larger world/environment reset;
- the underlying adjacent-frame discontinuity was large, approximately 29.5 grayscale MAE, around an order of magnitude larger than the normal frame-to-frame median;
- perceived discontinuity was substantially lower than the raw frame difference because the foreground occluder dominated visual attention;
- the occluder itself drifted in clothing brightness, texture, body geometry, blur and framing, causing a visible pop under close inspection.

Interpretation:

Occlusion can conceal major state changes, but the occluding object becomes the continuity-critical object and must itself be anchored.

## 6. Character continuity finding

The experiment maintained strong high-level character signals across the three generations:

- black sleeveless dress;
- dark hair;
- similar hairstyle;
- similar silhouette;
- frontal walking action;
- centered screen position;
- similar demeanor.

However, exact biometric, hair, body-proportion, wardrobe-detail and walk-cycle state still drifted.

Therefore, character continuity must distinguish:

- semantic/high-level identity continuity;
- exact visual identity continuity;
- exact performance/motion-state continuity.

Passing the first does not prove the latter two.

## 7. Motion continuity finding

The test demonstrated that motion continuity can be **concealed without being physically propagated**.

This is an important architectural distinction.

DreamMusicForge should not require exact stride, skeletal pose, arm phase, cloth motion and camera dynamics to propagate through every boundary when a cinematic concealment device can eliminate the need for the viewer to inspect those variables.

Where true continuity is required, those variables must be explicitly represented in the Boundary Contract and verified.

## 8. Spatial continuity finding

Spatial/world continuity was the largest fiction in the experiment, especially at the second boundary.

The environment after the foreground wipe changed substantially in openness, lighting, architectural proportions and subject-to-camera spatial relationship.

Therefore:

- do not call a sequence a true continuous take merely because the cut is hard to see;
- classify it as concealed continuity or a motivated scene transition when physical geography does not propagate.

## 9. Audio architecture

Audio must be treated as an independent continuous master timeline across the full cinematic sequence.

The visual renderer must not implicitly own the authoritative audio timeline merely because each generation contains audio.

Preferred architecture:

LONG-FORM MASTER AUDIO TIMELINE

- music
- dialogue
- narration
- ambience
- Foley
- footsteps
- sound effects
- designed transitions

under

SEGMENTED VISUAL GENERATIONS

Provider-generated audio may be harvested selectively where useful, but should not automatically replace or reset the master timeline.

### Experiment evidence

Approximate integrated loudness values for the three source clips were:

- clip 1: -27.5 LUFS
- clip 2: -47.3 LUFS
- clip 3: -32.3 LUFS

The source clips therefore had major loudness discontinuities. Around the stitched boundaries, measured short-window RMS energy changed by approximately -14.6 dB at the first handoff and +36.6 dB at the second.

Conclusion: in this experiment audio discontinuity was a greater technical weakness than the visual edit itself.

## 10. Editorial law for long takes

Do not create a 45/60/90-second continuous-looking shot simply because the generation system can.

Long duration must be justified by one or more of:

- emotional progression;
- narrative progression;
- performance value;
- suspense;
- revelation;
- choreography;
- environmental transformation;
- musical build/release;
- meaningful spatial experience;
- deliberate audience immersion.

Walter Murch Rule-of-Six priorities remain superior to technical continuity:

1. Emotion - 51%
2. Story - 23%
3. Rhythm - 10%
4. Eye Trace - 7%
5. Two-Dimensional Plane of Screen - 5%
6. Three-Dimensional Space - 4%

When tradeoffs are unavoidable, preserve higher priorities first.

## 11. Assembly and image-quality rule

- preserve the highest-quality available generated intermediates;
- avoid repeated delivery encodes between stitching stages;
- perform the final delivery encode at the end of assembly;
- maintain provenance for every source segment and transformation;
- distinguish prototype-quality media from delivery-quality media.

The August 28 stitched prototype remained 512x910, approximately 30 fps, H.264/AAC. It was suitable for continuity evaluation, not final delivery-quality proof.

## 12. Proposed 90-second architecture

A 90-second cinematic experience may be compiled as six approximately 15-second visual generations while preserving one global movie state and one continuous audio timeline.

Example:

- Segment A -> designed occlusion
- Segment B -> door cover
- Segment C -> normal editorial cut
- Segment D -> foreground wipe
- Segment E -> whip-pan concealment
- Segment F -> final reveal

The audience should experience one coherent cinematic sequence even though the renderer solves bounded generation windows.

The correct objective is not "six perfect continuations." The correct objective is "one verified coherent audience experience built from the most appropriate continuity strategy at each boundary."

## 13. Inspection and repair loop

For every boundary:

1. inspect source-end and target-start states;
2. measure visual mismatch where useful;
3. inspect character identity and performance drift;
4. inspect camera and spatial mismatch;
5. inspect audio continuity;
6. classify boundary type;
7. determine whether mismatch is visible to an ordinary viewer and under frame-by-frame scrutiny;
8. repair only the causal failure:
   - trim redundant overlap;
   - select a better match frame;
   - create bridge frames;
   - regenerate occluder;
   - regenerate target start state;
   - retime motion;
   - normalize/rebuild audio;
   - replace the boundary with a normal editorial cut if that is cinematically superior.

## 14. Verification and truth boundary

Claims must never exceed evidence.

For this continuity system, separately label evidence for:

- local simulation/assembly;
- provider dispatch;
- provider generation completion;
- character identity continuity;
- spatial continuity;
- semantic lip-sync;
- lyric/singing correctness;
- audio continuity;
- boundary invisibility;
- final creative quality.

Missing evidence cannot produce PASS.

A local simulation is not evidence that Kling or another provider generated the media.

## 15. Existing verified local milestone

The currently captured DreamMusicForge v5.0.0 evidence verifies a **local 90-second simulation artifact** containing:

- six 15-second visual sections;
- one continuous synthetic master audio track;
- five sampled stitch boundaries;
- a packaged scene ledger.

It does **not** by itself prove:

- live Kling/provider generation;
- Nola identity correctness;
- singing or lyric correctness;
- semantic lip-sync;
- final creative quality.

## 16. Development rule

Every verified DreamMusicForge/APEX build or material evidence-producing increment should be committed to GitHub with:

- version history;
- evidence;
- tests where applicable;
- truth boundary;
- rollback point.

GitHub publication itself must be verified before being claimed.
