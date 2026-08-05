# DreamMusicForge Benchmark Framework v0.1

This release turns renderer limitations into measurable engineering inputs.

## First benchmark

`DMF-B006 — Sustained Phrase Continuity`

Goal: prove that one singer, one wardrobe, one stage, one camera path, one song phrase, and one physical action can remain continuous across two provider-limited generations.

## Run

```bash
python -m dreammusicforge.benchmark_cli \
  dreammusicforge/benchmarks/benchmark_006_sustained_phrase.json \
  dreammusicforge/providers/kling/profile_v0.1.json \
  dreammusicforge/benchmarks/example_metrics_pass.json \
  --evidence-out dreammusicforge/evidence/run_0001/evidence.json \
  --profile-out dreammusicforge/evidence/run_0001/kling_profile_measured.json
```

Exit codes:

- `0`: benchmark passed
- `1`: benchmark executed but failed one or more thresholds
- `2`: benchmark or provider profile is invalid

## Promotion rule

Every critical dimension must meet its threshold. A high weighted average cannot compensate for identity, wardrobe, audio, or continuity failure.

## Current measurement boundary

v0.1 accepts externally measured 0–100 metrics and governs validation, scoring, provider-fit checks, evidence hashing, promotion decisions, and capability-profile updates.

Automated computer-vision and audio metric extraction are deliberately deferred to subsequent independently testable releases.
