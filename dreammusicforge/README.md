# DreamMusicForge Film Compiler

Provider-neutral AI music-video production pipeline, governed as an APEX
OCode module (`governance/DELEGATION_CONTRACT.yaml`). Built from
`DREAMMUSICFORGE FILM COMPILER — Application Specification v1.0` in
independently testable, reviewable releases -- see the spec's section 19
phased plan. **This README describes only what is actually built.**

## What exists today: Release 0.1 — Project Kernel, Release 0.2 — Master Song and Timeline, Release 0.3 — Film Genome

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
└── tests/music/              -- 108 tests, one file per module above
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

Release 0.3 adds `genome/`, the layer that turns performer, costume, and
world definitions plus declared genome-level facts (transformation arc,
camera language, color language, motifs, continuity invariants) into a
validated `FilmGenome` -- this release's acceptance test (spec section
19): "a complete Film Genome can be created and validated."

```
dreammusicforge/
├── genome/
│   ├── models.py    -- Performer, Costume, World, CameraLanguage,
│   │                     ColorLanguage, FilmGenome (frozen dataclasses,
│   │                     field shapes match spec section 6.3-6.6's
│   │                     example YAML exactly)
│   ├── schema.py     -- dict-shaped schemas + validate_*_schema() for
│   │                     each model; FilmGenome's validator also
│   │                     rejects a no-op transformation (from == to),
│   │                     duplicate motifs, and duplicate invariants
│   ├── ids.py          -- generate_performer_id/generate_costume_id/
│   │                     generate_world_id/generate_genome_id + is_valid_*
│   ├── errors.py        -- GenomeValidationError (DMFError)
│   └── builder.py        -- build_performer(), build_costume(),
│                          build_world(), assemble_film_genome()
└── tests/genome/          -- 67 tests, one file per module above
```

```python
from dreammusicforge.genome import (
    build_performer, build_costume, build_world, assemble_film_genome,
    CameraLanguage, ColorLanguage,
)

performer = build_performer(
    display_name="Nola",
    reference_assets=("face_front.png", "full_body_front.png"),
    immutable={"apparent_age": "late 20s", "face_geometry": "oval, high cheekbones",
               "body_proportions": "average, athletic", "skin_tone": "warm olive",
               "eye_color": "dark brown", "identifying_features": "small mole above lip"},
    mutable_by_contract={"expression": "varies by shot", "pose": "varies by shot",
                          "gaze": "varies by shot", "costume": "varies by shot",
                          "hair_configuration": "varies by shot"},
)
costume = build_costume(
    topology={"neckline": "symmetrical_square", "sleeves": "none"},
    material="satin", references={"front": "costume_front.png"}, embroidery="geometric_gold",
)
world = build_world(
    type="physical_theatrical_stage", references={"wide": "stage_wide.png"},
    geometry="proscenium stage, 12m wide", palette="deep blue with amber accents",
    lighting="single key light, cool wash", atmosphere="light haze",
)

genome = assemble_film_genome(
    transformation_from="concealment", transformation_to="self-expression",
    performers=(performer,), costumes=(costume,), worlds=(world,),
    camera_language=CameraLanguage(lens_vocabulary=("35mm", "50mm"), movement_vocabulary=("slow_push", "controlled_orbit")),
    color_language=ColorLanguage(opening="amber_crimson", development="blue_pearl", climax="red_gold"),
    motifs=("threshold", "circular_opening", "hand_to_heart"),
    invariants=("lead_performer_identity", "master_song", "narrative_transformation"),
)
```

`assemble_film_genome()` derives `performer_ids`/`costume_ids`/`world_ids`
directly from the `Performer`/`Costume`/`World` objects it's given, so a
`FilmGenome` built through it cannot reference a nonexistent entity --
spec Law 3.7 ("fail closed" on missing references) enforced structurally,
by construction, rather than by an after-the-fact existence check. See
`genome/schema.py`'s module docstring for the boundary that leaves stated
(referential integrity for a `FilmGenome` loaded from a dict of unknown
provenance, rather than built through this function).

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
  -s dreammusicforge/tests/music` (108 tests), `python -m unittest
  discover -s dreammusicforge/tests/genome` (67 tests), and `python -m
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
- **Genome entity ids don't match the spec's own example ids.** Spec
  section 6.4-6.6's YAML shows human-authored-looking ids like
  `COSTUME-RED-001` and `WORLD-BLUE-STAGE-001`. This release keeps the
  same machine-generated `PREFIX-<8 hex chars>` convention established
  in `core/ids.py` and extended in `music/ids.py` (`generate_id()` /
  `is_valid_id()`) rather than inventing a second id format -- the
  spec's YAML is illustrative of the *shape* of the data, not a format
  requirement, and one consistent id convention across the whole
  application is worth more than matching an example's cosmetics.
- **`Performer.immutable` and `.mutable_by_contract` are `dict[str, str]`
  free-text fields, not enums.** Spec section 6.4's YAML shows keys like
  `apparent_age` and `expression` with no value (a template, not a
  closed vocabulary), so this release validates that every required key
  is present with a non-empty descriptive string and does not invent a
  fixed set of allowed values for any of them -- that would be scope the
  spec doesn't authorize here.
- **`FilmGenome`'s referential integrity is structural, not a runtime
  check.** `assemble_film_genome()` builds `performer_ids`/
  `costume_ids`/`world_ids` directly from the `Performer`/`Costume`/
  `World` objects passed to it, so there's no code path in this release
  where a `FilmGenome` built through the public API could reference an
  entity that doesn't exist. `validate_film_genome_schema()` alone (e.g.
  on a dict loaded from storage in a later release) can only check that
  referenced ids are well-formed, not that they exist -- stated in
  `genome/schema.py`'s module docstring as an intentional boundary this
  release doesn't close, since closing it needs a registry of real
  entities to check against, which doesn't exist yet.

### What Release 0.2 deliberately does not include

Real audio analysis of any kind: no beat/onset detection, no key or tempo
estimation, no automatic section (verse/chorus) detection, no lyric
transcription or forced alignment, no stem separation -- `stems` on
`MasterSong` is a dict of paths a human or an earlier pipeline stage
supplies, not something this release produces. All of that is exactly the
kind of DSP work the spec defers to later stages; nothing here claims to
do it.

Unlike Release 0.1, there is no persistence layer or CLI for this
release's domain objects: `MasterSong` and `Timeline` exist only as
in-memory dataclasses returned by `music/builder.py` -- there is no
`MasterSongRepository` and no `dmf` CLI subcommand to build, save, or
load one. A caller that wants to persist a `MasterSong` today has to
serialize `.to_dict()` itself. Wiring that up is straightforward
(`storage/sqlite_repository.py`'s `ProjectRepository` is a template for
exactly this) but wasn't part of this release's authorized scope.

Production Graph (0.4), Renderer Capability Atlas (0.5), Video Slicer
(0.6), provider compilers (0.7+), verification, repair, assembly, and
the Operator Studio web interface (0.15) remain unbuilt, per the spec's
own phased plan -- none of that is stubbed out here, per the spec's own
rule against labeling provisional logic as production logic.

### What Release 0.3 deliberately does not include

No `Project` integration: `Project.film_genome_id` (added in Release
0.1) is still an unresolved forward reference -- nothing in this release
writes a `FilmGenome`'s id back onto a `Project`, and there's no CLI
subcommand to build a genome interactively. No persistence layer either,
same gap as Release 0.2's `MasterSong`/`Timeline`: `Performer`, `Costume`,
`World`, and `FilmGenome` exist only as in-memory dataclasses returned by
`genome/builder.py`.

No prop, movement-language, or motif-registry entities as separate
first-class models. The spec's architecture diagram (section 5) shows
`genome/prop/`, `genome/movement_language/`, and `genome/motif_registry/`
as their own subpackages, but section 19's Release 0.3 "Build" list names
only performer, costume, world, motif, camera language, and invariants --
and the one worked example (section 6.3's `film_genome` YAML) represents
`props` as a flat list on `World` and `motifs` as a flat list of strings
on `FilmGenome`, with no richer structure shown for either. This release
follows the worked example rather than the architecture diagram where
they disagree, consistent with Release 0.1/0.2's "flat modules, not
premature subpackages" choice (see "Design choices worth knowing about"
above) -- promote to real entities if a later release's requirements
demand it.

No continuity *enforcement*: `invariants` on `FilmGenome` is a validated
list of non-empty, unique strings (e.g. `lead_performer_identity`,
`master_song`), but nothing in this release checks that a shot, clip, or
generated asset actually honors a declared invariant -- that's
Production Graph (0.4) and the verification stages named in the spec's
pipeline diagram (section 2), not this one.

## The original, pre-spec governed baseline

`runtime.py` and `dmf_ir/` predate this specification and are unrelated
to it -- see `TESTING.md` for their own test instructions. Nothing in
Release 0.1, Release 0.2, or Release 0.3 imports from, depends on, or
modifies either.
