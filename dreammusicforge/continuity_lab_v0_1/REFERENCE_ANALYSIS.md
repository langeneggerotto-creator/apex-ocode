# Reference Video Reverse Engineering — APEX Continuity Lab v0.1

Status: evidence-bounded frame analysis of the supplied screen recording.

## Technical profile

- Duration: 235.6667 s
- Video: H.264, 1106×512, 30 fps
- Audio: AAC stereo, 44.1 kHz
- The first/last seconds contain screen/player UI and are excluded from cinematic-grammar conclusions.

## Core finding

The reference does **not** use one transition trick. Its perceived smoothness comes from selecting a transition mechanism that matches the physical/compositional situation. The movie alternates among:

1. true continuous spatial motion;
2. portals/thresholds where the incoming world is already visible inside an aperture;
3. full-frame foreground occlusion hiding a cut/world reset;
4. material/texture transformation that removes stable landmarks;
5. graphic matches that preserve shape/eye trace while content changes;
6. motion/flash blur that makes exact geometry temporarily unreadable;
7. ordinary editorial cuts when story/rhythm benefit from an obvious section change.

The system therefore must choose a boundary archetype before generation. A universal dissolve is structurally wrong.

## Observed transition grammar

### T01 — ~6.2–10.5 s — Nested frame portal
The camera advances into a framed image. The new world exists inside a bounded rectangle before that rectangle becomes the full viewport.

### T02 — ~21.7–23.2 s — Diegetic frame recomposition
A physical frame becomes a strong compositional boundary around the performer and creates an eye-trace reset.

### T03 — ~31.4–34.2 s — Character-led spatial carry
The performer remains the visual anchor while the camera/background relationship changes into a corridor. Identity, wardrobe, footwear, body scale, screen position, motion phase, camera velocity, horizon and lens behavior must stay coherent.

### T04 — ~37.0–40.2 s — Doorway threshold carry
The camera follows through a doorway. The next room appears through the doorway before filling the frame.

### T05 — ~50.6–52.1 s — Curtain full-coverage wipe
Fabric crosses close to lens. The environment may change only while coverage is near-total/full. The same fabric trajectory/texture must continue across the handoff.

### T06 — ~89.7–90.2 s — Intentional hard cut
A red/orange section cuts directly to a blue section. The visual adjacent-frame difference is large (~33.9 grayscale MAE at analysis scale) and sampled short-window audio level changes by roughly -8 dB. This is a deliberate editorial reset, not failed continuity.

### T07 — ~126.8–127.7 s — Water/material → circular graphic match
A water/splash field overwhelms stable landmarks. Circular life-preserver geometry emerges from that material with the new composition centered inside it. Raw visual peak is high (~31.6 MAE), yet shape, motion and eye trace preserve perceptual flow.

### T08 — ~165.7–167.6 s — Clapperboard full-coverage wipe
A physical prop fills the lens. Once coverage is full, the world can reset behind it.

### T09 — ~183.9–185.0 s — Feather/material color morph
Foreground feather/fabric texture rises into the camera. While the image is dominated by material, hue/texture migrate from muted/brown to orange/red, then reveal the next environment. This is a canonical continuity-safe-zone transition.

### T10 — ~201.9–203.0 s — Costume/material bridge
Large costume/feather mass plus a dark vertical occluder carries motion between environments. If wardrobe changes, the transformation must occur under occlusion, not after reveal.

### T11 — ~219.2–220.5 s — Whip/flash/foreground bridge
Fast body/camera motion and a bright cool flash hide a large frame discontinuity. The raw peak is the largest measured (~46.5 MAE), yet stable landmarks vanish at the decision point. Match direction/speed and cut at maximum blur/flash.

### T12 — ~220.5–225.0 s — Doorway/room reveal
The camera carries through darkness/threshold into a new room and changes elevation/angle progressively rather than jumping subject scale.

## Why the previous three-clip experiment failed

The prior stitch attempted to hide boundaries after incompatible clips already existed. The viewer could compare face/identity, footwear, wardrobe detail, body proportions, subject frame height, camera distance, lens/perspective, stride phase, environment landmarks and vanishing point.

Those variables must be either **identical at the boundary** or **fully unavailable to the viewer while they change**. Editing cannot create state continuity that source generations never possessed.

## Hard continuity state vector

`IDENTITY_ID, FACE_STATE, HAIR_STATE, MAKEUP_STATE, BODY_PROPORTIONS, WARDROBE_ID, FOOTWEAR_ID, SUBJECT_SCREEN_X, SUBJECT_SCREEN_Y, SUBJECT_FRAME_HEIGHT, CAMERA_DISTANCE, CAMERA_HEIGHT, FOCAL_BEHAVIOR, HORIZON, SCREEN_DIRECTION, MOTION_PHASE, VELOCITY, LIGHTING_DIRECTION, EXPOSURE_INTENT`

If the target start violates a hard invariant, regenerate. Do not disguise it with a dissolve.

## Perceptual safe-zone rule

1. establish moving occluder/material/portal;
2. increase coverage or blur;
3. suppress stable landmarks;
4. reach the decision zone, often ≥95% coverage or maximum blur/flash;
5. perform the actual generation handoff;
6. maintain the same occluder/motion field for several frames;
7. reveal the target world with locked character/camera state.

## Audio finding

Most reference transitions have modest sampled short-window RMS changes (roughly within a few dB), supporting one continuous master audio bed across visual portal transitions. The intentional section cut near 90 s is an exception with a substantially larger level change.

## Verification doctrine

A transition may pass only if hard identity/wardrobe/footwear invariants match when required; subject scale/screen position/action phase are within tolerance; camera axis and screen direction are coherent; world reset occurs inside the declared safe zone; masking is sufficient; crossfade ghosting is absent; stable landmarks do not pop; audio is continuous or intentionally authored; and both normal-speed and frame-by-frame review pass their appropriate criteria.
