# DreamMusicForge Film Compiler

Provider-neutral AI music-video production pipeline, governed as an APEX
OCode module (`governance/DELEGATION_CONTRACT.yaml`). Built from
`DREAMMUSICFORGE FILM COMPILER — Application Specification v1.0` in
independently testable, reviewable releases -- see the spec's section 19
phased plan. **This README describes only what is actually built.**

## What exists today: Release 0.1 — Project Kernel, Release 0.2 — Master Song and Timeline

The one domain object this release ships is `Project` (spec section 6.1):
id, title, version, status, aspect ratio, resolution, frame rate, target
duration, provider list, and forward references (currently unresolved) to
a master song, film genome, and production graph that later releases will
populate.

```
dreammusicforge/
├── core/
│   ├── models.py    -- Project (frozen dataclass), PROJECT_STATUSES
│   ├── schema.py     -- PROJECT_SCHEMA (dict) + validate_project_schema()
│   ├── ids.py         -- generate_project_id() / validate_project_id()
│   ├── hashing.py    -- sha256 helpers (hash_bytes/hash_text/hash_file)
│   ├── paths.py       -- confine_path(): the one place a filesystem path
│   │                     gets constructed from user input, anywhere in this module
│   └── errors.py      -- typed error hierarchy, all deriving from DMFError
├── storage/
│   └── sqlite_repository.py -- ProjectRepository (create/save/get/list_projects)
├── apps/cli/
│   └── main.py        -- `dmf project init|validate|show`
└── tests/kernel/       -- 61 tests, one file per module above
```

### Try it

```bash
cd apex-ocode
python3 -m dreammusicforge.apps.cli.main project init "Begin Again" --workspace /tmp/my_film --provider kling --provider veo
python3 -m dreammusicforge.apps.cli.main project validate /tmp/my_film/project.json
python3 -m dreammusicforge.apps.cli.main project show <the id printed above> --workspace /tmp/my_film
```

`project init` creates a `Project`, schema-validates it, persists it to a
SQLite database at `<workspace>/.dreammusicforge/kernel.db`, and writes the
same data as `<workspace>/project.json` -- the JSON file is the portable,
human-readable form; the database is the queryable index. Both are
produced from the same `Project.to_dict()` call, so they can never drift
from each other by construction.

Release 0.2 adds `music/`, the layer that turns one audio file plus a few
declared facts into a canonical timeline (spec section 19's acceptance
test for this release: "one song can become a canonical timeline").

```
dreammusicforge/
├── music/
│   ├── models.py         -- MasterSong, Section, Beat, LyricLine, Timeline
│   │                         (frozen dataclasses, same to_dict/from_dict
│   │                         convention as core/models.py's Project)
│   ├── schema.py          -- dict-shaped schemas + validate_*_schema()
│   │                         for each model, plus timeline-level checks
│   │                         (chronological order, no overlapping
│   │                         sections or lyric lines)
│   ├── wav_inspector.py  -- inspect_wav(): real duration/sample-rate/
│   │                         channel metadata from a WAV file, stdlib
│   │                         `wave` module only
│   ├── timecode.py        -- seconds <-> HH:MM:SS:FF, seconds <-> (bar, beat)
│   ├── frames.py           -- seconds <-> frame-number
│   ├── beats.py            -- generate_beats(): deterministic beat grid
│   │                         from a declared bpm/time-signature/offset
│   ├── ids.py               -- generate_audio_id/generate_section_id/
│   │                         generate_lyric_id + is_valid_*
│   ├── errors.py            -- AudioInspectionError, InvalidTimecodeError,
│   │                         TimelineValidationError (all DMFError)
│   └── builder.py           -- build_master_song(), build_beats_for_song(),
│                              assemble_timeline() -- the assembly layer
│                              that ties the modules above together
└── tests/music/              -- 105 tests, one file per module above
```

```python
from pathlib import Path
from dreammusicforge.music import build_master_song, build_beats_for_song, assemble_timeline
from dreammusicforge.music.models import Section, LyricLine

song = build_master_song(Path("begin_again.wav"), bpm=120.0, time_signature="4/4")
beats = build_beats_for_song(song, beats_per_bar=4)
timeline = assemble_timeline(
    song,
    sections=(Section(id="SECTION-1", type="verse", start_seconds=0.0, end_seconds=20.0),),
    beats=beats,
    lyric_lines=(LyricLine(id="LYRIC-1", start_seconds=0.0, end_seconds=3.0, text="a placeholder lyric line"),),
)
```

`build_master_song()` reads real metadata from the WAV file and hashes its
bytes; `bpm` and `time_signature` are declared inputs, not derived --
see "What Release 0.2 deliberately does not include" below.
`assemble_timeline()` validates the result against `music/schema.py`
before returning it and raises `TimelineValidationError` (carrying every
problem found, not just the first) if it wouldn't pass.

### Design choices worth knowing about

- **Flat modules, not subpackages, for `core/ids`, `core/hashing`,
  `core/errors`.** The spec's architecture diagram (section 5) shows these
  with trailing slashes, which could be read as subpackages. They're
  single files here because each is currently small (under 60 lines) and
  a directory with one `__init__.py` doing the same job as a `.py` file is
  premature structure. Promote to a real subpackage when one of them
  actually grows enough to need it.
- **No `jsonschema` dependency.** `core/schema.py` is a plain dict walked
  by hand in `validate_project_schema()`, matching the convention already
  established in this repository's sibling `dreammusicforge` module (in
  the separate `agentic-twin` repository) and keeping this module's
  dependency list at zero third-party packages.
- **`argparse`, not `click`/`typer`.** Same reasoning: stdlib-only. Worth
  revisiting once the CLI surface grows past a handful of subcommands.
- **`Project` is frozen.** Every "mutation" (see
  `with_updated_timestamp()`) returns a new instance. No code anywhere in
  this release holds a `Project` and mutates a field in place.
- **`pyproject.toml` describes packaging metadata only.** `pip install`
  has not been run against it in this environment. What has been verified
  to work, repeatedly, is `python -m unittest discover -s
  dreammusicforge/tests/kernel` (61 tests), `python -m unittest discover
  -s dreammusicforge/tests/music` (105 tests), and `python -m
  dreammusicforge.apps.cli.main` from the repository root -- none require
  an installation step.
- **`core/ids.py` gained generic `generate_id(prefix)` /
  `is_valid_id(value, prefix)` in Release 0.2**, so the new `AUDIO-`,
  `SECTION-`, and `LYRIC-` id families in `music/ids.py` don't duplicate
  the prefix/token logic. `generate_project_id()` /
  `validate_project_id()` / `is_valid_project_id()` are now thin wrappers
  over the generic functions -- behavior is byte-for-byte unchanged (all
  61 pre-existing kernel tests pass unmodified against the refactored
  file).
- **`music/wav_inspector.py` is WAV-only, not a general audio prober.**
  A format decoder covering mp3/aac/flac/etc. needs either ffmpeg as an
  external binary dependency or a third-party package -- this release
  introduces neither speculatively. Spec section 6.2's example
  `source_file` is itself a `.wav`.
- **Beat-grid generation is arithmetic, not audio analysis.**
  `music/beats.py`'s `generate_beats()` computes where beats *would* fall
  given a declared bpm, time signature, and offset -- it does not detect
  beats from the audio itself (no onset detection, no tempo tracking).
  That's real DSP work; the spec's section 8.1 names `librosa` for
  exactly this, as part of a later external-assembly-pipeline release.
  Tempo is also assumed constant for the whole song -- if it genuinely
  varies, this model does not represent that, stated here rather than
  silently gapped.
- **`Timeline` validation checks chronological order and rejects
  overlapping sections or lyric lines**, but does not cross-check
  section/lyric boundaries against the `MasterSong`'s own
  `duration_seconds` -- a section ending after the song ends is not yet
  caught. Worth adding once a release actually needs that guarantee.

### What Release 0.2 deliberately does not include

Real audio analysis of any kind: no beat/onset detection, no key or tempo
estimation, no automatic section (verse/chorus) detection, no lyric
transcription or forced alignment, no stem separation -- `stems` on
`MasterSong` is a dict of paths a human or an earlier pipeline stage
supplies, not something this release produces. All of that is exactly the
kind of DSP work the spec defers to later stages; nothing here claims to
do it. Film Genome (0.3), Production Graph (0.4), Renderer Capability
Atlas (0.5), Video Slicer (0.6), provider compilers (0.7+), verification,
repair, assembly, and the Operator Studio web interface (0.15) remain
unbuilt, per the spec's own phased plan -- none of that is stubbed out
here, per the spec's own rule against labeling provisional logic as
production logic.

## The original, pre-spec governed baseline

`runtime.py` and `dmf_ir/` predate this specification and are unrelated
to it -- see `TESTING.md` for their own test instructions. Nothing in
Release 0.1 or Release 0.2 imports from, depends on, or modifies either.
