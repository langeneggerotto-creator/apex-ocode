# DreamMusicForge Media Execution Engine v0.1

This subsystem converts an approved `AssemblyManifest` into an allowlisted FFmpeg execution plan and optionally executes it inside a caller-provided workspace.

## Canonical boundary

Media execution is mechanical. It may normalize, concatenate, mute provider audio, lay back the canonical master song, hash outputs, and report failures. It may not change Film Genome, Experience Graph, Production Twin, verification decisions, shot order, or creative intent.

## v0.1 rules

- only `ffmpeg` is allowlisted
- provider audio must be muted
- the external master song is authoritative
- asset order comes only from the Assembly Manifest
- only hard CUT transitions are executable in v0.1
- unsupported transitions fail closed rather than silently degrading
- output paths are simple file names; path traversal is rejected
- dry-run is the default execution mode
- successful real execution emits SHA-256 evidence

## Deliberate gaps

This release does not yet implement dissolves, wipes, compositing, color matching, lip-sync processing, loudness mastering, automatic seam measurement, evidence-ledger persistence, or CLI orchestration. Those remain separate independently testable increments.
