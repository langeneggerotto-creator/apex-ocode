# Film Genome Specification v0.1

## Definition

The Film Genome is the smallest complete semantic specification capable of regenerating a film at equivalent meaning, identity, continuity, musical, narrative, and experiential fidelity.

It is not a prompt, storyboard, screenplay, timeline, or rendered video. It is the compact governing source from which DMF-IR and all downstream artifacts are compiled.

## Required Domains

- purpose and transformation objective
- target audience and intended viewer change
- characters and identity invariants
- worlds, props, wardrobe, and persistent entities
- narrative states and causal event graph
- song identity, structure, lyrics, rhythm, harmony, energy, and emotional curve
- semantic events and weights
- continuity and mutation rules
- cinematic language
- recurring motifs and symbols
- provider-independent constraints
- success, ambiguity, and falsification criteria
- evidence and lineage requirements

## Compilation Boundary

```text
Film Genome → validate → DMF-IR → compile → provider packages
```

The Film Genome states what must remain true. DMF-IR states how that truth is represented as typed executable objects. Provider adapters state how a renderer is instructed.

## Minimum Regeneration Test

A Film Genome passes only if a memoryless implementation can reconstruct:

1. the same transformation objective;
2. the same persistent identities and worlds;
3. the same causal narrative;
4. the same song-governed temporal structure;
5. the same permitted and prohibited state changes;
6. the same intended viewer inferences;
7. equivalent downstream DMF-IR without relying on hidden context.
