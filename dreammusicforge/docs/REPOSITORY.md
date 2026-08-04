# DreamMusicForge Repository Map

## Current Location

DreamMusicForge is currently a governed module inside `langeneggerotto-creator/apex-ocode`.

## Ownership

- **OCode:** governance, delegation contracts, repository confinement, provider orchestration, tests, evidence, rollback, Git and release controls.
- **DreamMusicForge:** Film Genome, DMF-IR, compilers, verification, benchmarks, evidence-producing production workflows.
- **Video providers:** rendering backends. They do not own meaning, continuity, canonical state, or evidence.

## Current Baseline

```text
dreammusicforge/
├── README.md
├── __init__.py
├── runtime.py
├── TESTING.md
├── constitution/
├── docs/
├── governance/
├── examples/
└── tests/
```

## Split Trigger

Move DreamMusicForge into a dedicated repository when at least two of these are true:

- it requires independent release cadence;
- it has multiple provider adapters and services;
- its CI or dependency graph materially diverges from OCode;
- it exceeds the governance-wrapper role of the current repository;
- independent contributors or deployments require separate permissions.

Until then, all work remains bounded to `dreammusicforge/**` unless an approved cross-module integration contract explicitly permits otherwise.
