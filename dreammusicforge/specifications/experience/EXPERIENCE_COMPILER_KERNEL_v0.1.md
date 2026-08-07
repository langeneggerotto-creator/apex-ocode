# Experience Compiler Kernel v0.1

Status: NEXT EXECUTABLE BUILD

## Objective
Create the first executable top-level compiler that transforms a bounded human-intent brief into a deterministic Experience Graph consumed by narrative, music, camera, lighting, editing, and production compilers.

## Inputs
- purpose
- audience
- beginning audience state
- desired ending audience state
- transformation objective
- target duration
- optional emotional landmarks
- master-song timeline reference when available

## Output
```yaml
experience_graph:
  version: 0.1
  duration_seconds:
  transformation:
    from:
    to:
  checkpoints:
    - t_start:
      t_end:
      primary_experience:
      secondary_experiences: []
      intensity: 0.0
      attention_goal:
      memory_goal:
      intended_inference:
      prohibited_inference: []
      evidence_status:
```

## Rules
1. Experience describes intended audience state, not camera or shot instructions.
2. Downstream compilers may implement the graph but may not silently redefine it.
3. Checkpoints must cover the timeline without undeclared gaps or overlaps.
4. Intensity is normalized 0..1.
5. Every inferred psychological claim must carry evidence status; the kernel must not claim validated psychology from intuition.
6. Deterministic validation must fail closed on missing transformation, invalid timing, invalid intensity, or contradictory checkpoints.

## Initial Package
```text
dreammusicforge/experience/
  __init__.py
  models.py
  validator.py
  compiler.py
  schema.json
  tests/
```

## CLI
```text
dmf experience validate experience.json
dmf experience compile brief.json --out experience_graph.json
```

## Acceptance
- typed models
- JSON schema
- deterministic validation
- complete timeline coverage
- stable serialization
- tests for valid, gap, overlap, invalid intensity, missing transformation, and contradictory checkpoint cases
- no renderer/provider dependency
- no LLM dependency in kernel v0.1

## Non-Goals
Narrative generation, shot design, renderer prompting, audience prediction, and emotional-effect claims are explicitly out of scope for v0.1.
