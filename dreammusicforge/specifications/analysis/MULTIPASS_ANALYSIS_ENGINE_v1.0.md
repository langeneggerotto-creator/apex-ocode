# DreamMusicForge Multi-Pass Analysis Engine v1.0

## Execution graph

VIDEO
→ PASS 0 Ingest + Evidence Freeze
→ PASS 1 Technical Analysis
→ PASS 2 Visual / Production Analysis
→ PASS 3 Performance Analysis
→ PASS 4 Music + Editorial Analysis
→ PASS 5 Continuity Seam Audit
→ PASS 6 Production / Renderer Feasibility
→ PASS 7 Compiler Synthesis
→ FINAL SYNTHESIS

## Output contract
Every pass emits:
- `analysis/pass_NN.json` — machine-readable truth
- `analysis/pass_NN.md` — human-readable interpretation

Every claim carries one truth label: VERIFIED, MEASURED, INFERRED, POSSIBLE, UNKNOWN.

## Analysis contract
The 24-section Master Music Video Analysis specification remains the complete coverage contract. Specialized passes are the execution mechanism. The final synthesis MUST reconcile pass outputs without silently resolving contradictions. Conflicts must be preserved and surfaced.

## Continuity model
Continuity is not one score. It contains:
- pixel continuity
- state continuity
- causal continuity
- semantic continuity

Audio/music continuity contains:
- audio continuity
- musical continuity
- vocal continuity
- performance continuity

## Required compiler outputs
The final compiler pass must convert observations into executable DreamMusicForge artifacts where evidence supports them:
- Film Genome
- Production Graph
- Shot Contracts
- Transition Contracts
- Renderer Tasks
- Assembly Tasks
- Verification Contracts
- Learning Principles
- Engineering Backlog

## Renderer feasibility
All renderer recommendations must route through the capability atlas and carry evidence status. The Analysis Engine may recommend decomposition, compositing, editorial illusion, specialist processing, or redesign instead of forcing direct generation.

## Benchmark role
A reference analysis is not an imitation instruction. It extracts production functions, relationships, constraints, and quality patterns to support original future productions.
