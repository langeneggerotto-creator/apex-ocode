# DreamMusicForge Assembly Engine v0.1

The Assembly Engine is the deterministic boundary between accepted production assets and the final sequence timeline.

## Responsibilities

- sort accepted assets by canonical film time
- reject timeline gaps and overlaps
- require one transition contract for every adjacent asset pair
- preserve an uninterrupted external master song as final audio authority
- mute provider-generated audio by default
- declare normalization targets for resolution, frame rate, codec and pixel format
- emit seam records for downstream continuity verification
- produce a provider-neutral assembly manifest

## Canonical Rules

1. Only accepted assets may enter assembly.
2. Asset ordering is derived from canonical timeline state, not filenames or upload order.
3. The final soundtrack is the canonical external master song.
4. Provider audio is muted by default.
5. Every seam is explicit and must be verified downstream.
6. Assembly may not rewrite Film Genome, Experience Graph, Production Twin or verification truth.
7. Missing timeline coverage, overlaps, transition contracts or master-audio coverage fail closed.

## Current Boundary

v0.1 compiles a deterministic assembly manifest. It does not yet invoke FFmpeg, perform compositing, execute transitions, color-match shots, lip-sync performers, or render a final video file.
