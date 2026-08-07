# Digital Film Twin and Canonical Ontology v1.0

Status: CANONICAL-DRAFT

## Purpose
The Digital Film Twin is the canonical simulation of the intended film before and during rendering. Renderers approximate the twin; the twin never derives truth from an unverified renderer output.

## Core Entities
Dream; Transformation; Audience; Experience; Story; Character; Performer; World; Costume; HairMakeupState; Prop; Motif; Music; Lyric; Beat; Scene; Shot; Slice; Transition; State; Camera; Lighting; Color; Motion; Emotion; Meaning; Verification; Evidence.

## Relationship Model
Film contains Sequences; Sequence contains Scenes; Scene contains Shots; Shot contains Actions and Slices; Action changes State; State changes observable reality; observable reality supports intended Meaning; Meaning contributes to Audience Experience.

## Canonical Time Slice
```yaml
time_slice:
  absolute_time:
  frame:
  beat:
  bar:
  lyric:
  sequence_id:
  scene_id:
  shot_id:
  performer_states: []
  camera_state:
  lighting_state:
  world_state:
  prop_states: []
  emotional_intent:
  audience_experience_target:
```

## State Machines
Persistent entities must expose legal transitions. Examples include performer state, camera state, lighting state, costume state, prop state, narrative state, and emotional state. A generated candidate that implies an illegal transition is a causal-continuity failure unless an explicit transition contract authorizes it.

## Continuity Invariants
Identity, master-song position, approved costume topology within its continuity window, approved world geometry within its continuity window, and active motif lineage are explicit state variables rather than prose assumptions.

## Renderer Boundary
A render task receives a bounded projection of the Digital Film Twin containing only the state required to execute that task. The provider may not become the canonical state authority.
