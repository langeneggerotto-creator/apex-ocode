# DreamMusicForge Production Strategy Engine v0.1

This kernel converts an intended Production Twin transition plus a renderer capability profile into one deterministic production strategy.

## Strategies

- `DIRECT_RENDER`
- `CONTROLLED_CONTINUATION`
- `LAYERED_COMPOSITING`
- `EDITORIAL_ILLUSION`
- `EXTERNAL_SPECIALIST_STAGE`
- `REDESIGN_REQUIRED`

## Design rules

1. Fail closed on invalid inputs.
2. Never route unsupported critical identity requirements to optimistic direct rendering.
3. Long continuous takes use controlled continuation only when renderer state inheritance is available.
4. High character count and extreme choreography are decomposed into layers when possible.
5. Missing native lip sync routes to a dedicated specialist stage when available.
6. Editorial illusion is a valid production strategy when the intended audience experience can be preserved with motivated cuts.
7. The engine is provider-neutral and contains no Kling-specific prompt logic.

The engine intentionally does not generate prompts. Provider compilers consume the selected strategy later.
