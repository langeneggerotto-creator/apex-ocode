# DreamMusicForge Renderer Capability Atlas v0.1

The Capability Atlas converts renderer evidence into production decisions.

It does not ask whether a renderer is generally "good." It asks whether a specific renderer is fit for a specific shot under explicit quality thresholds.

## Inputs

- renderer capability profile;
- shot duration;
- required continuity and production capabilities;
- complexity penalties;
- evidence status for each capability.

## Outputs

- fit score;
- risk band;
- acceptance decision;
- explicit failures;
- required mitigations;
- ranked renderer recommendations.

## Governing rules

1. Provider duration limits are hard constraints.
2. Critical continuity failures cannot be averaged away.
3. Unknown capability evidence fails visibly rather than being silently assumed.
4. Complexity reduces expected reliability.
5. Profiles marked `ASSUMED_UNTIL_BENCHMARKED` are planning aids, not proof.
6. Benchmark evidence must replace assumptions over time.

## Reference-standard production interpretation

The uploaded benchmark standard should be decomposed into renderer-fit shot families:

- low-risk: solo hero close-ups, slow pushes, atmospheric tableaux, symbolic inserts;
- moderate-risk: controlled walking, compact choreography, short lip-sync passages, simple multi-shot sequences;
- high-risk: exact costume continuity across generations, long camera continuation, several interacting performers;
- very-high-risk: mass choreography, four-minute global memory, independent song generation across clips, autonomous professional editing.

DreamMusicForge should route low-risk shots directly, simplify or externally control moderate-risk shots, layer/composite high-risk shots, and prohibit unsupported very-high-risk requests.

## Test command

```bash
python -m unittest dreammusicforge.tests.test_capability_atlas -v
```
