# DreamMusicForge Architecture

## Compiler Stack

```text
Human Intent
→ Transformation Compiler
→ Meaning Compiler
→ Narrative Compiler
→ Music Compiler
→ Reality Compiler
→ Continuity Compiler
→ Cinematic Compiler
→ Provider Compiler
→ Verification Engine
→ Evidence Ledger
→ Canonical Film
```

## Canonical Artifacts

1. **Film Genome** — smallest complete semantic specification capable of regenerating the film while preserving governing invariants.
2. **DMF-IR** — typed, executable, provider-neutral representation compiled from the Film Genome.
3. **Provider Package** — provider-specific prompts, references, constraints, and generation settings.
4. **Continuity Packet** — verified state exported by one accepted clip and inherited by the next.
5. **Evidence Run** — immutable record of inputs, outputs, checks, metrics, decisions, hashes, and known gaps.

## Quality Gate

Every compiler follows:

```text
Input → Validate → Compile → Verify → Record Evidence → Promote or Reject
```

No compiler may bypass validation, verification, or evidence recording.

## Package Boundaries

```text
dreammusicforge/
├── constitution/
├── schemas/
├── ontology/
├── film_genome/
├── dmf_ir/
├── compilers/
│   ├── transformation/
│   ├── meaning/
│   ├── narrative/
│   ├── music/
│   ├── lyrics/
│   ├── beat/
│   ├── reality/
│   ├── continuity/
│   ├── transition/
│   ├── cinematography/
│   ├── choreography/
│   ├── editing/
│   └── provider/
│       ├── kling/
│       ├── veo/
│       └── runway/
├── verification/
├── runtime/
├── cli/
├── studio/
├── benchmarks/
├── research/
├── evidence/
├── tests/
└── docs/
```

## Provider Boundary
Provider adapters may translate DMF-IR into a target provider's supported controls. They may not redefine meaning, rewrite continuity, or silently weaken constitutional constraints.
