# DreamMusicForge Production Twin v0.1

The Production Twin is the canonical dynamic state model for a film in progress. The Film Genome defines persistent creative DNA; the Production Twin defines how that DNA evolves over time.

## v0.1 scope

This increment implements deterministic, provider-neutral state tracking for:

- performer identity, costume, hair, pose, gaze, action and emotion;
- camera state;
- lighting and palette state;
- canonical master-song position and energy;
- intended audience experience;
- world geometry and prop state;
- invariants and explicitly permitted mutations.

Adjacent states are connected by declared transitions. Validation fails closed on timeline gaps/overlaps, undeclared mutations, invariant violations, invalid normalized values, missing transitions and master-timeline mismatch.

The compiler converts validated adjacent states into provider-neutral RendererTaskContract objects. Provider adapters such as Kling must consume those contracts downstream; provider-specific assumptions do not belong in this kernel.

## Canonical distinction

Film Genome = static creative DNA.

Production Twin = dynamic canonical reality through time.

Rendered asset = evidence-bearing approximation of a requested Production Twin transition.

No renderer output may redefine canonical state merely because it generated differently.

## Not yet implemented

- automatic construction from Experience Graph;
- 3D spatial coordinates or physics simulation;
- provider adapters;
- render-result comparison against intended state;
- CLI wiring;
- persistence/database layer;
- automatic QA models.

Those are separate releases.
