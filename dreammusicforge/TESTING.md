# DreamMusicForge Testing

Run from the repository root:

```bash
python -m unittest discover -s dreammusicforge/tests -v
```

Expected baseline: 6 tests passing.

The tests verify:

- valid DMF project acceptance;
- last-frame seed handoff;
- state-inheritance failure;
- provider duration-limit failure;
- action-complexity failure;
- preservation of music as the master clock.

No provider generation is claimed by this test suite. It verifies deterministic compilation behavior only.
