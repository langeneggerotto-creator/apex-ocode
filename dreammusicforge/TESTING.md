# DreamMusicForge Testing

Run from the repository root. There are two independent suites, one per module
(this repo's existing test layout requires a `-s` pointed directly at each
test directory -- see the discovery note below):

```bash
python -m unittest discover -s dreammusicforge/tests -v
python -m unittest discover -s dreammusicforge/dmf_ir/tests -v
```

Expected baseline: 6 tests passing in `dreammusicforge/tests`, 22 in
`dreammusicforge/dmf_ir/tests` (28 total).

## dreammusicforge/tests (runtime.py -- the original lightweight compiler)

- valid DMF project acceptance;
- last-frame seed handoff;
- state-inheritance failure;
- provider duration-limit failure;
- action-complexity failure;
- preservation of music as the master clock.

## dreammusicforge/dmf_ir/tests (DMF-IR v1 -- schema, validator, models, compiler)

- schema validation: missing top-level/nested required fields rejected, non-dict input rejected, `schema_version` is optional and defaults correctly;
- clip state inheritance: state-inheritance failure, every clip imports exactly one source state, source/destination reality-state timecodes must match the clip's start/end;
- checks new in DMF-IR (beyond `runtime.validate_project`): a clip that needs a predecessor cannot be first in the timeline; `film.duration_seconds` must match the last clip's end time; the music timeline must be contiguous (no gaps/overlaps) and must span the full film duration; semantic/music events attached to a clip must actually overlap that clip's time window; `required_reference_assets` must resolve to a known character or world; verification-contract `pass_threshold` must be in `(0, 1]`;
- Kling provider compilation / final-frame handoff, expressed provider-neutrally: clip ordering, first-clip-has-no-dependency, `last_frame_seed` -> `verified_end_frame` dependency on the correct predecessor (the same guarantee `runtime.py`'s `test_last_frame_handoff` checks, without a Kling-specific filename), compiled clips resolve full objects rather than bare ids, required-reference ids are de-duplicated, and the compiled plan carries no provider-specific fields (no "Kling", no `.mp4`, no `-VERIFIED-END.png`);
- `runtime.py`'s existing behavior is completely unaffected by DMF-IR's presence (re-run directly in the DMF-IR suite as a regression guard, in addition to `dreammusicforge/tests` itself still passing unmodified).

No provider generation is claimed by either test suite. Both verify deterministic compilation behavior only.
