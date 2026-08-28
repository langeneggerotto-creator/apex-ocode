# DreamMusicForge Video Technique Knowledge Bank

Status: CANONICAL RESEARCH BANK / IMPLEMENTATION INPUT
Date: 2026-08-28
Scope: reusable filmmaking, AI-generation, editing, transition, camera, framing, aspect-ratio, compositing, color, audio, and verification techniques for DreamMusicForge / APEX Movie Forge.

## 1. Governing principle

Seamlessness is not a single transition effect. It is the result of preserving or deliberately masking every viewer-visible continuity variable that can reveal a boundary.

The system must therefore distinguish:

- true state continuity;
- perceptually concealed continuity;
- motivated editorial transitions;
- ordinary cuts that are intentionally visible but cinematically correct.

No post-production effect can fully repair two source clips whose character identity, wardrobe, footwear, body scale, camera distance, lens perspective, motion phase, world geometry, lighting, or screen direction are incompatible.

## 2. Research sources incorporated

### Runway / AI-video generation

- Runway, Creating with Seedance 2.0: https://help.runwayml.com/hc/en-us/articles/50488490233363-Creating-with-Seedance-2-0
- Runway, Creating with Seedance 2.5: https://help.runwayml.com/hc/en-us/articles/53542207042323-Creating-with-Seedance-2-5
- Runway, Using reference media: https://help.runwayml.com/hc/en-us/articles/52963720640275-Using-reference-media-to-guide-your-generations
- Runway, Creating with Edit Studio: https://help.runwayml.com/hc/en-us/articles/51683104370451-Creating-with-Edit-Studio
- Runway, Aleph 2.0 Prompting Guide: https://help.runwayml.com/hc/en-us/articles/52150503729171-Aleph-2-0-Prompting-Guide
- Runway Academy, Video Transformation with Aleph: https://academy.runwayml.com/course/video-magic-aleph
- Runway, How to create longer videos and films: https://help.runwayml.com/hc/en-us/articles/26871350018835-How-to-create-longer-videos-and-films
- Runway, Kling 3.0 Motion Control: https://help.runwayml.com/hc/en-us/articles/50280558448147-Creating-with-Kling-3-0-Motion-Control
- Runway, Introduction to Workflows: https://help.runwayml.com/hc/en-us/articles/45763528999699-Introduction-to-Workflows
- Runway, Utility Nodes in Workflows: https://help.runwayml.com/hc/en-us/articles/47184761711379-Using-Utility-Nodes-in-Workflows

### Adobe Premiere / After Effects

- Match cuts: https://www.adobe.com/creativecloud/video/post-production/cuts-in-film/match-cut.html
- J/L cuts: https://helpx.adobe.com/be_en/premiere/desktop/edit-projects/trim-clips/perform-j-cuts-and-l-cuts.html
- Track masks: https://helpx.adobe.com/premiere/desktop/add-video-effects/work-with-masks/track-masks.html
- Scene Edit Detection: https://helpx.adobe.com/premiere/desktop/edit-projects/change-clip-sequence/detect-edit-points-using-scene-edit-detection.html
- Match color between shots: https://helpx.adobe.com/premiere/desktop/correct-color/add-color-effects/match-color-between-shots.html
- Optical Flow / time interpolation: https://helpx.adobe.com/in/premiere/desktop/edit-projects/change-clip-speed/apply-time-interpolation-methods-to-adjust-clip-speed.html
- Speed / duration: https://helpx.adobe.com/premiere/desktop/edit-projects/change-clip-speed/change-clip-speed-using-the-speedduration-option.html
- Warp Stabilizer: https://helpx.adobe.com/premiere/desktop/add-video-effects/commonly-used-effects/stabilize-shaky-footage-using-warp-stabilizer.html
- Auto Reframe: https://helpx.adobe.com/premiere/desktop/add-video-effects/commonly-used-effects/add-auto-reframe-effect-to-a-sequence.html
- Multicamera synchronization: https://helpx.adobe.com/premiere/desktop/edit-projects/set-up-multi-camera-sequences-for-editing/mark-clips-for-synchronization.html
- Multicamera editing: https://helpx.adobe.com/ca/premiere/desktop/edit-projects/set-up-multi-camera-sequences-for-editing/create-and-edit-a-multi-camera-target-sequence.html
- Audio crossfades: https://helpx.adobe.com/premiere/desktop/add-audio-effects/apply-audio-transitions/audio-crossfade-transitions.html
- Auto-match audio loudness: https://helpx.adobe.com/premiere/desktop/add-audio-effects/adjust-volume-and-levels/auto-match-audio-loudness.html
- 3D Camera Tracker: https://helpx.adobe.com/ie/after-effects/using/tracking-3d-camera-movement.html
- Object Matte / rotoscoping: https://helpx.adobe.com/after-effects/desktop/roto-brush-and-refine-matte/roto-brush/object-matte.html
- Content-Aware Fill: https://helpx.adobe.com/ph_fil/after-effects/how-to/remove-unwanted-element.html

### Blackmagic Design / DaVinci Resolve

- Official DaVinci Resolve training: https://www.blackmagicdesign.com/products/davinciresolve/training
- Fairlight: https://www.blackmagicdesign.com/products/davinciresolve/fairlight
- Edit page: https://www.blackmagicdesign.com/products/davinciresolve/edit

### Cinematic grammar / continuity references

- StudioBinder, editing transitions / invisible cuts: https://www.studiobinder.com/blog/types-of-editing-transitions-in-film/
- Continuity editing: https://www.studiobinder.com/blog/what-is-continuity-editing-in-film/
- Screen direction: https://www.studiobinder.com/blog/what-is-screen-direction-in-film/
- 180-degree rule: https://www.studiobinder.com/blog/what-is-the-180-degree-rule-film/
- Eyeline match: https://www.studiobinder.com/blog/what-is-an-eyeline-match/
- Match-on-action: https://www.studiobinder.com/blog/what-is-a-match-on-action-cut/
- Whip-pan transitions: https://www.studiobinder.com/blog/swish-pan-whip-pan-definition-film/
- Camera-shot / angle / movement taxonomy: https://www.studiobinder.com/blog/ultimate-guide-to-camera-shots/

## 3. AI-generation controls that must become first-class Movie Forge controls

### 3.1 Reference-media anchoring

Use separate persistent references for:

- character identity;
- face;
- full-body proportions;
- hair;
- wardrobe;
- footwear;
- hero props;
- environment;
- lighting/look;
- camera-motion reference;
- performance/motion reference;
- audio/pacing reference.

Character plates should include front, side/profile, back, full body, and footwear-visible views where continuity matters. Environment plates should establish geometry, materials, key landmarks, vanishing points, and lighting from multiple angles.

### 3.2 First-frame and last-frame anchoring

Use first/last-frame control when exact boundary state matters.

Preferred chain:

SEGMENT N actual last frame
-> canonical boundary frame
-> SEGMENT N+1 literal first frame

The first frame is a hard continuity anchor; ordinary references only guide appearance and must not be treated as equivalent.

### 3.3 Video-reference motion transfer

Use video references to preserve:

- body motion;
- gesture timing;
- expression timing;
- camera movement;
- blocking;
- rhythm;
- scene structure.

For motion-control workflows, source performance footage should be a clean, single continuous shot with the whole relevant body visible where possible. Character proportions should match the performance reference.

### 3.4 Extend-video operations

Prefer model-supported forward/backward extension over independent regeneration when the next span is intended to be physically continuous. Extension should still be verified for identity, wardrobe, footwear, scale, environment geometry, and motion drift.

### 3.5 Keyframe-driven editing

For targeted repairs, select a keyframe that clearly exposes the defect, edit only the requested element, preview the keyframe, then propagate the edit through the clip. Useful repairs include:

- footwear correction;
- wardrobe correction;
- background correction;
- prop continuity;
- lighting consistency;
- character-detail repair.

### 3.6 Workflow locking

Lock/reuse outputs and settings that define continuity:

- character references;
- environment references;
- seed where supported;
- aspect ratio;
- FPS;
- resolution;
- canonical first/last frames;
- camera plan;
- audio timeline.

Do not regenerate verified anchors unnecessarily.

## 4. Continuity state vector

Every shot and every boundary should expose a machine-readable state vector.

### Character

- CHARACTER_ID
- FACE_STATE
- HAIR_STATE
- MAKEUP_STATE
- WARDROBE_STATE
- FOOTWEAR_STATE
- ACCESSORY_STATE
- BODY_PROPORTIONS
- SILHOUETTE
- SKIN_TONE_RENDER_STATE
- EXPRESSION
- GAZE
- HEAD_ORIENTATION
- BODY_POSE
- HAND_STATE
- LEFT_FOOT_PHASE
- RIGHT_FOOT_PHASE
- ARM_SWING_PHASE
- LOCOMOTION_VELOCITY
- CLOTH_MOTION_STATE

### Camera

- CAMERA_POSITION_XYZ
- CAMERA_ORIENTATION
- CAMERA_HEIGHT
- FOCAL_LENGTH / FOV
- SENSOR / projection assumption where relevant
- CAMERA_DISTANCE_TO_SUBJECT
- CAMERA_VELOCITY
- CAMERA_ACCELERATION
- PAN / TILT / ROLL
- DOLLY / TRUCK / CRANE / ORBIT state
- ZOOM state
- HORIZON_POSITION
- SUBJECT_SCREEN_XY
- SUBJECT_FRAME_HEIGHT_PERCENT
- HEADROOM
- LEAD_ROOM
- DEPTH_OF_FIELD
- FOCUS_DISTANCE
- MOTION_BLUR / shutter appearance

### World / environment

- WORLD_ID
- SPACE_ID
- GEOMETRY_STATE
- VANISHING_POINT(S)
- FLOOR_PLANE
- WALL / DOOR / PORTAL state
- LANDMARK positions
- PROP positions
- LIGHT_SOURCE directions
- LIGHT_INTENSITY
- COLOR_TEMPERATURE
- EXPOSURE
- ATMOSPHERE
- WEATHER
- PARTICLE state
- OCCLUDER state

### Editorial / temporal

- GLOBAL_TIMECODE
- SHOT_ID
- SCENE_ID
- ACTION_PHASE
- BEAT_PHASE
- TRANSITION_TYPE
- SCREEN_DIRECTION
- 180_DEGREE_AXIS
- EYELINE
- EYE_TRACE_TARGET
- EXPECTED_NEXT_FRAME_STATE

### Audio

- MASTER_AUDIO_TIMECODE
- MUSIC_PHASE
- TEMPO / BEAT
- DIALOGUE_STATE
- AMBIENCE_STATE
- ROOM_TONE
- FOLEY_PHASE
- FOOTSTEP_PHASE
- SFX_STATE
- REVERB / SPACE state
- LOUDNESS

## 5. Transition taxonomy for generation and editing

### 5.1 Hard cut

Use when the cut itself should be invisible through narrative expectation, action continuity, or rhythm. Do not add a transition merely because two clips meet.

### 5.2 Match on action

Cut during an action and continue the same action phase in the next shot. Track pose, direction, velocity, limb phase, object position, and screen-space trajectory.

### 5.3 Graphic match

Match dominant shape, line, silhouette, color block, framing, or composition across shots.

### 5.4 Eyeline match

Preserve eyeline, shot size, camera distance, focal length, horizon, and depth-of-field relationships so the viewer reconstructs one coherent space.

### 5.5 Sound bridge / J-cut / L-cut

Carry audio across the visual boundary to make the scene transition perceptually continuous. The master audio timeline should not restart at visual-generation boundaries.

### 5.6 Full-frame occlusion invisible cut

Move behind or into a wall, pillar, person, prop, hair, fabric, darkness, vehicle, smoke, water, feather mass, or other surface until continuity-sensitive information is no longer visible. Perform the actual handoff inside the maximum-coverage safe zone.

### 5.7 Foreground wipe

A foreground subject/object crosses the lens. The occluder becomes continuity-critical and must match in trajectory, speed, direction, scale, lighting, blur, texture, and silhouette across both clips.

### 5.8 Whip-pan / swish-pan transition

Match:

- pan direction;
- angular speed;
- acceleration/deceleration profile;
- blur density;
- exposure;
- color where physical continuity is intended;
- reveal timing.

The actual cut should occur near maximum motion blur.

### 5.9 Texture-fill transition

Use water, smoke, fabric, hair, feathers, particles, crowd, darkness, flare, fog, or similar texture to dominate the frame. The reference-video analysis shows this can hide very large world changes if the viewer cannot inspect stable landmarks during the handoff.

### 5.10 Light / flash / overexposure transition

Drive highlights toward clipping or a flare/flash that suppresses scene detail, change state while detail is unavailable, then recover into the new scene. Match color temperature and temporal decay.

### 5.11 Door / portal transition

Use a closing/opening door, elevator, curtain, hatch, or architectural portal. If the door surface is visible at the cut, its geometry, seams, lighting, texture, and camera distance must match.

### 5.12 Camera-behind-object transition

Move the camera behind architecture or a foreground object. Preserve camera velocity and parallax entering and exiting the mask.

### 5.13 Rack-focus transition

Shift attention via focus between foreground/background or subjects. Use only when motivated; focus distance and blur evolution become temporal continuity variables.

### 5.14 Speed-ramp transition

Retime motion into/out of a boundary. Use optical-flow interpolation only when motion topology is suitable and verify for warping, doubled limbs, or texture tearing.

### 5.15 Dissolve / morph

Use only when the story wants visible temporal/spatial blending. Do not use long dissolves to hide generation mismatch; they often create double bodies, double backgrounds, and ghosting.

### 5.16 Cutaway / insert

When exact continuity cannot be solved, cut to a motivated detail or reaction, then return to a regenerated state. This is often superior to a technically strained invisible transition.

## 6. Camera and composition knowledge bank

### Shot sizes

- extreme wide / establishing;
- wide / full;
- medium-wide;
- medium;
- medium close-up;
- close-up;
- extreme close-up;
- insert / detail.

### Angles

- eye level;
- high angle;
- low angle;
- overhead / bird's-eye;
- worm's-eye;
- Dutch angle;
- over-the-shoulder;
- POV;
- profile / three-quarter / frontal / rear.

### Camera movement

- static;
- pan;
- tilt;
- whip pan;
- dolly in/out;
- truck/track left-right;
- pedestal up/down;
- crane/jib;
- orbit/arc;
- Steadicam/gimbal;
- handheld;
- zoom;
- dolly zoom;
- push/pull with subject;
- pass-through / portal move.

### Composition variables

- rule of thirds;
- central/symmetrical composition;
- leading lines;
- negative space;
- headroom;
- look room / lead room;
- horizon position;
- dominant diagonal;
- foreground/midground/background layering;
- frame-within-frame;
- eye trace;
- subject-frame occupancy;
- balance of visual mass.

### Spatial continuity laws

- preserve screen direction unless intentionally broken;
- preserve the 180-degree axis for spatial clarity;
- match eyelines;
- avoid accidental left/right reversals;
- when changing angle within the same action, preserve action phase and screen-space direction;
- avoid small unmotivated angle changes that create jump-cut feel;
- if a boundary claims true continuity, lens perspective and subject-camera distance must be consistent, not merely subject pixel size.

## 7. Identity / wardrobe / footwear continuity

The attached three-clip experiment exposed footwear as a high-salience continuity detector.

Therefore exact continuity requires separate verification of:

- face;
- hair;
- makeup;
- dress/top/bottom;
- sleeves/straps;
- jewelry;
- bags/props;
- shoes/boots/heels;
- shoe color;
- heel height;
- toe shape;
- straps/laces;
- sole profile;
- body scale;
- limb proportions.

A generic statement such as "same woman in same black dress" is insufficient.

## 8. Aspect ratio, framing, proportions, and delivery

Aspect ratio is a canonical project state, not a final crop decision.

Track at least:

- source ratio;
- target ratio;
- target resolution;
- safe action region;
- safe text/title region;
- subject-screen occupancy;
- focal point;
- camera-space framing intent.

When adapting between 16:9, 9:16, 1:1, 4:5, etc., prefer intelligent reframing or outpainting over arbitrary crop. Re-verify headroom, footwear visibility, hand visibility, look room, and motion path after reframe.

## 9. Post-production repair toolkit

### Detection / analysis

- Scene Edit Detection to recover original cuts;
- frame-by-frame review;
- reference/current split view;
- scopes and waveform/vectorscope;
- optical flow analysis;
- mask/object tracking;
- 3D camera tracking;
- motion-vector continuity;
- audio waveform and loudness analysis.

### Visual repair

- precise trim / slip / slide / roll edits;
- position/scale alignment;
- color match and manual grade;
- exposure/white-balance matching;
- tracked masks;
- object mattes / rotoscoping;
- content-aware removal/fill;
- camera stabilization;
- motion retiming;
- optical-flow interpolation;
- tracked compositing;
- selective foreground/background replacement;
- grain/noise matching;
- sharpening/blur matching;
- motion-blur matching.

### Audio repair

- one continuous master audio timeline;
- J/L cuts;
- constant-power or other appropriate crossfades;
- loudness matching;
- room-tone beds;
- ambience continuity;
- Foley continuity;
- footstep phase;
- reverb matching;
- dialogue repair / ADR;
- music beat alignment;
- designed whoosh/impact only when motivated.

## 10. Verification model

Do not optimize a single frame-difference number.

Each boundary should be scored across:

### Perceptual invariants

- character identity consistency;
- wardrobe consistency;
- footwear consistency;
- body-proportion consistency;
- subject scale;
- screen position;
- camera distance;
- lens/perspective;
- horizon;
- screen direction;
- motion phase;
- motion velocity;
- environment geometry;
- landmark consistency;
- lighting/exposure/color;
- focus/depth of field;
- motion blur;
- audio continuity.

### Masking / concealment

- frame coverage percentage;
- landmark visibility suppression;
- motion blur;
- texture entropy;
- occluder consistency;
- safe-zone duration;
- eye-trace displacement;
- reveal timing.

### Artifact penalties

- ghosting;
- double bodies;
- duplicated limbs;
- object morphing;
- warping;
- optical-flow tearing;
- exposure pop;
- color-temperature pop;
- scale jump;
- footwear change;
- facial drift;
- environment reset;
- audio jump;
- reverb-space change.

Verification must include both normal-speed viewing and frame-by-frame inspection. A boundary that passes only when paused but looks bad in motion, or vice versa, is not a full pass.

## 11. Reference-video findings to preserve

The August 28, 2026 attached reference demonstrates that professional seamlessness frequently comes from *authored transition geometry* rather than dissolves.

Observed transition archetypes include:

- foreground or texture filling the frame;
- a clapperboard occupying the frame and revealing a new world beneath it;
- warm hair/feather-like texture filling the image before revealing a red stage;
- large foreground props such as life-preserver shapes crossing the camera;
- camera/subject motion carrying the eye through hard editorial cuts;
- ordinary hard cuts used where rhythm/story outweigh literal continuity.

The key lesson is that a high-quality video can mix true continuous movement, concealed cuts, match-on-action, foreground wipes, graphic matches, hard cuts, and audio bridges. The system must select the technique per boundary rather than force every boundary into a single transition style.

## 12. Canonical boundary compiler

For every planned boundary:

1. classify intent: TRUE_CONTINUOUS_SPAN / CONCEALED_CONTINUITY_SPAN / MOTIVATED_SCENE_TRANSITION / EDITORIAL_CUT;
2. freeze canonical character/world/camera/audio state;
3. select a transition archetype;
4. generate a Boundary Contract;
5. determine what MUST remain invariant;
6. determine what MAY change;
7. determine when the change is allowed to occur;
8. generate/extend/edit the two participating spans from shared anchors;
9. assemble with one master audio timeline;
10. run objective and perceptual verification;
11. repair only the failing variable;
12. do not promote to PASS until critical unknowns are resolved.

## 13. Tutorial-routing matrix

When the production problem is:

- identity drift -> reference images / character plates / keyframe repair;
- wardrobe or shoes drift -> full-body reference + keyframe edit + exact first-frame anchor;
- camera-distance mismatch -> camera-state lock + reference-video motion + position/scale only as last-resort post repair;
- environment mismatch -> environment plates + shared last/first frames + world-state lock;
- motion mismatch -> match-on-action + motion reference + optical-flow retime if topology permits;
- foreground wipe mismatch -> trajectory/scale/blur match + tracked occluder compositing;
- whip transition mismatch -> match pan direction/speed/blur + cut at maximum blur;
- visible world change -> increase perceptual coverage or replace with a motivated editorial cut;
- color/exposure mismatch -> comparison view + scopes + color match/manual grade;
- shaky camera -> stabilize, then re-evaluate crop/perspective;
- aspect-ratio adaptation -> Auto Reframe/outpaint + reverify composition;
- sound jump -> continuous master timeline + loudness match + J/L or crossfade;
- missing ambience -> room tone / environmental bed / Foley;
- unwanted object -> tracked mask / object matte / content-aware removal;
- different camera angle needed from same source -> targeted in-context angle generation, then verify spatial and character consistency;
- longer contiguous footage needed -> extend-video first; independent regeneration only if extension fails or story requires reset.

## 14. Research-bank rule

This file is a living canon. New tutorials or techniques should be added only when they produce one or more of:

- a new controllable generation primitive;
- a new transition archetype;
- a better continuity invariant;
- a better repair method;
- a better verification metric;
- a documented provider capability/limitation;
- a repeatable workflow that improves final audience-visible quality.

Tutorial knowledge must be operationalized into contracts, algorithms, tests, or review criteria. Merely collecting links is not considered integration.
