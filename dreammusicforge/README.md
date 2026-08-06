# DreamMusicForge Film Compiler

Provider-neutral AI music-video production pipeline, governed as an APEX
OCode module (`governance/DELEGATION_CONTRACT.yaml`). Built from
`DREAMMUSICFORGE FILM COMPILER — Application Specification v1.0` in
independently testable, reviewable releases -- see the spec's section 19
phased plan. **This README describes only what is actually built.**

## What exists today: Release 0.1 — Project Kernel, Release 0.2 — Master Song and Timeline, Release 0.3 — Film Genome, Release 0.4 — Production Graph, Release 0.5 — Renderer Capability Atlas, Release 0.6 — Video Slicer, Release 0.7 — Kling Compiler, Release 0.8 — Candidate Intake and Evidence, Release 0.9 — Technical Verification, Release 0.10 — Acceptance and Repair Engine, Release 0.11 — Assembly Engine

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

Release 0.4 adds `production/`, the layer that turns `Sequence`,
`SemanticEvent`, and `Shot` definitions plus a `FilmGenome` into a
validated, time-ordered `ProductionGraph` -- this release's acceptance
test (spec section 19): "project compiles into an ordered production
graph."

```
dreammusicforge/
├── production/
│   ├── models.py    -- SemanticEvent, Sequence, Shot (with nested
│   │                     ShotTiming/ShotPurpose/ShotRequirements/
│   │                     ShotContinuity), ProductionGraph
│   ├── schema.py     -- dict-shaped schemas + validate_*_schema() for
│   │                     each model; ProductionGraph's validator is
│   │                     where Release 0.4's "dependencies" and
│   │                     "transition relationships" deliverables live:
│   │                     no two shots may overlap in time, every shot's
│   │                     sequence_id/semantic_event_id must resolve
│   │                     inside the same graph, and consecutive
│   │                     same-performer shots in the same sequence must
│   │                     chain state (one shot's destination_state must
│   │                     equal the next shot's inherited_state)
│   ├── ids.py          -- generate_sequence_id/generate_semantic_event_id/
│   │                     generate_shot_id/generate_graph_id + is_valid_*
│   ├── errors.py        -- ProductionGraphValidationError (DMFError)
│   └── builder.py        -- build_semantic_event(), build_sequence(),
│                          build_shot(), assemble_production_graph()
└── tests/production/      -- 64 tests, one file per module above
```

```python
from dreammusicforge.production import build_semantic_event, build_sequence, build_shot, assemble_production_graph
from dreammusicforge.production.models import ShotTiming, ShotPurpose, ShotRequirements, ShotContinuity

event = build_semantic_event(
    start_seconds=42.0, end_seconds=48.5, meaning="confidence becomes declaration",
    transformation_from="uncertainty", transformation_to="agency",
    intended_viewer_inference=("she has chosen to be seen",), required_visible_evidence=("direct gaze",),
)
sequence = build_sequence(song_section="chorus_1", start_seconds=40.0, end_seconds=60.0)

shot = build_shot(
    sequence_id=sequence.id,
    timing=ShotTiming(start_seconds=42.0, end_seconds=48.5, song_section="chorus_1", lyric_ids=("LYRIC-018",)),
    purpose=ShotPurpose(semantic_event_id=event.id, narrative_function="declaration", editorial_function="chorus_hero_shot"),
    requirements=ShotRequirements(
        performer_id=performer.id, costume_id=costume.id, world_id=world.id,
        lip_sync_required=True, choreography_complexity="medium", camera_motion="slow_push", character_count=1,
    ),
    continuity=ShotContinuity(inherited_state="concealed", permitted_mutations=("gaze",), destination_state="revealed"),
    acceptance={"identity": 95.0, "camera_intent": 90.0},
)

graph = assemble_production_graph(film_genome=genome, sequences=(sequence,), semantic_events=(event,), shots=(shot,))
```

`Shot` deliberately carries only `timing`/`purpose`/`requirements`/
`continuity`/`acceptance` -- not `renderer_risk`, `slice_strategy`,
`slices`, or `editing`, even though spec section 6.8's worked example
shows all of those on one `shot` object. Those fields are Video Slicer
(0.6) outputs that come *after* Production Graph in the pipeline (spec
section 2); producing them here would mean claiming a later release's
integration. `ShotContinuity` (`inherited_state`/`permitted_mutations`/
`destination_state`) is this release's own addition, not shown in
section 6.8's YAML -- it exists to satisfy Law 3.5's explicit
requirement that "every shot must declare: inherited state; permitted
mutations; expected destination state" and mirrors the
`source_state_id`/`destination_state_id` chaining this same
repository's pre-spec `runtime.py` already validates for exactly this
purpose (see `production/models.py`'s module docstring).

`assemble_production_graph()` checks that every shot's
`requirements.performer_id`/`costume_id`/`world_id` actually exists in
the given `FilmGenome` -- the one check `production/schema.py` cannot
make on its own, since a `FilmGenome` isn't part of the
`production_graph` dict -- and sorts the resulting `shots` by
`timing.start_seconds`, which is what "compiles into an *ordered*
production graph" means here: the compiler imposes the order, callers
don't have to pre-sort their input.

Release 0.5 adds `capability_atlas/`, the layer that turns declared
per-provider capabilities into a ranked, per-shot provider-fit report --
this release's acceptance test (spec section 19): "shot requirements
produce a provider-fit report."

```
dreammusicforge/
├── capability_atlas/
│   ├── models.py    -- RendererCapability, RendererCapabilityProfile,
│   │                     ShotFitScore, ProviderFitReport
│   ├── schema.py     -- dict-shaped schemas + validate_*_schema() for
│   │                     capability and profile
│   ├── scoring.py     -- score_capability_status() (a pure function
│   │                     from Law 3.10's five-way status to a number),
│   │                     evaluate_shot_fit(), rank_providers_for_shot()
│   ├── errors.py       -- CapabilityAtlasValidationError (DMFError)
│   └── builder.py       -- build_capability(), build_capability_profile()
└── tests/capability_atlas/  -- 47 tests, one file per module above
```

```python
from dreammusicforge.capability_atlas import build_capability, build_capability_profile, rank_providers_for_shot

kling = build_capability_profile(
    provider="kling", max_duration_seconds=15.0, max_character_count=3,
    supported_camera_motions=("slow_push", "static"),
    capabilities=(build_capability("identity", "verified"), build_capability("lip_sync", "measured")),
)
veo = build_capability_profile(
    provider="veo", max_duration_seconds=6.0, max_character_count=1, supported_camera_motions=("slow_push",),
)

report = rank_providers_for_shot(shot, (veo, kling))  # shot from Release 0.4
report.recommended_provider   # "kling" -- veo is disqualified (shot duration exceeds its 6s limit)
```

`evaluate_shot_fit()` treats a shot's `requirements` (duration derived
from `timing`, `character_count`, `camera_motion`, `lip_sync_required`)
as hard disqualifiers -- a provider that structurally cannot render the
shot gets `overall_score` 0.0 outright, no partial credit. Providers that
pass are scored on every capability *named in the shot's own
`acceptance` dict* (spec section 6.8's threshold keys, e.g. `identity`,
`lip_sync`): a capability the profile doesn't declare at all scores 0.0
for that dimension rather than being silently skipped, so the report
always shows exactly what evidence is and isn't behind a ranking.
`score_capability_status()`'s numbers (100 / 80 / 55 / 0 / 0) are this
release's own interpretation, not spec-mandated -- see
`capability_atlas/scoring.py`'s module docstring for the reasoning,
including why `unsupported` and `unknown` deliberately score the same.

Release 0.6 adds `slicer/`, the layer that turns a `Shot` and its
`ProviderFitReport` (Release 0.5) into a validated `SliceResult` of
executable render tasks -- this release's acceptance test (spec section
19): "complex shot becomes executable render tasks."

```
dreammusicforge/
├── slicer/
│   ├── models.py    -- RiskFactors, TemporalSlice, VisualLayer,
│   │                     MotionLayer, FallbackPlan, RenderTask,
│   │                     StrategyDecision, SliceResult
│   ├── schema.py     -- dict-shaped schemas + validate_*_schema() for
│   │                     each model
│   ├── risk.py         -- compute_risk_factors(): deterministic risk
│   │                     scoring built from Shot + RendererCapabilityProfile
│   │                     + ShotFitScore (Release 0.5's own output)
│   ├── strategy.py      -- select_strategy(): four of spec section
│   │                     7.4's five named strategies, computed
│   │                     deterministically (see below for the fifth)
│   ├── errors.py          -- SlicerValidationError (DMFError)
│   └── builder.py          -- slice_shot(): the top-level orchestration
└── tests/slicer/            -- 57 tests, one file per module above
```

```python
from dreammusicforge.capability_atlas import rank_providers_for_shot
from dreammusicforge.slicer import slice_shot

report = rank_providers_for_shot(shot, (kling, veo))  # shot/profiles from Releases 0.4-0.5
result = slice_shot(shot, report, {"kling": kling, "veo": veo})

result.strategy       # "direct_render" | "controlled_continuation" | "layered_compositing" | "external_production_required"
result.render_tasks   # one or more RenderTask, each with a RENDER-* id, provider, duration, required_assets
```

`select_strategy()` never returns `editorial_illusion`: spec section
7.4's own "Select when" bullets for it ("symbolic imagery can replace
literal complexity," "cutaways can conceal defects") are creative
judgments with no computable signal in this repository's domain model.
Auto-selecting it would mean fabricating a proxy for a human creative
call -- exactly the placeholder logic spec section 22 forbids labeling
complete. `controlled_continuation` is selected only when a provider was
disqualified *purely* for exceeding the shot's duration and it declares
positive-evidence support for a continuation-style capability
(`video_extension`/`last_frame_seed`, reusing this same repository's
pre-spec `runtime.py` continuity-mode vocabulary) -- `slice_shot()` then
chunks the shot into as many `<= max_duration_seconds` pieces as needed,
chaining each `RenderTask` after the first to the previous one's output
file. `layered_compositing` produces a small, deliberately modest set of
visual layers (`world_pass`, `performer_pass`, and `lip_sync_pass` when
required) -- see "What Release 0.6 deliberately does not include" for
why finer per-character layers aren't attempted.

Release 0.7 adds `providers/kling/`, the first provider-specific
package -- it turns a `RenderTask` (Release 0.6) plus its `Shot`
(Release 0.4) into an operator-usable `KlingPackage`: a real prompt, a
negative prompt, a selected mode, and a resolved reference manifest.
This release's acceptance test (spec section 19): "each task produces
an operator-usable Kling package."

```
dreammusicforge/
├── providers/
│   ├── __init__.py   -- namespace only; spec section 14's
│   │                     provider-neutral VideoRenderer interface is
│   │                     not implemented anywhere yet (see below)
│   └── kling/
│       ├── models.py    -- KlingProfile, KlingPackage
│       ├── schema.py     -- dict-shaped schemas + validate_*_schema()
│       ├── compiler.py    -- compile_kling_package(),
│       │                     compile_kling_packages()
│       ├── errors.py       -- KlingCompilerError (DMFError)
│       └── ids.py            -- generate_kling_package_id() + is_valid_*
└── tests/providers/kling/      -- 29 tests, one file per module above
```

```python
from dreammusicforge.providers.kling import KlingProfile, compile_kling_packages

profile = KlingProfile(max_duration_seconds=15.0)
packages = compile_kling_packages(slice_result.render_tasks, shot, profile)  # render_tasks/shot from Releases 0.4-0.6

packages[0].mode              # "image_to_video" or "video_extension"
packages[0].prompt            # a full, structured prompt string
packages[0].negative_prompt   # a fixed baseline negative-prompt list
```

Mode selection is one rule, deterministically applied: a `RenderTask`
whose `required_assets` includes a `.mp4` reference is a continuation
task (Release 0.6's `controlled_continuation` strategy chains every task
after the first to the previous one's output file), so it compiles to
`video_extension`; everything else compiles to `image_to_video`, since
Performer/Costume/World reference assets (Release 0.3) are reference
images. If the resulting mode isn't declared in the given `KlingProfile.
supported_modes`, compilation fails closed instead of silently picking
something unsupported.

The prompt template is not invented from nothing: it adapts this same
repository's pre-spec `runtime.py`'s `compile_kling_packages()` --
same structural pattern (explicit continuity statement, explicit "do
not perform future actions," explicit preservation list), rewritten
against the new typed `Shot` fields instead of `runtime.py`'s
dict-shaped clips. `KLING_NEGATIVE_PROMPT_BASELINE` is copied from that
same function verbatim. See `providers/kling/compiler.py`'s module
docstring for the full mapping.

Release 0.8 adds `generation/`, the layer that imports a rendered
candidate file and makes it independently verifiable rather than merely
asserted -- this release's acceptance test (spec section 19): "every
imported candidate is traceable."

```
dreammusicforge/
├── generation/
│   ├── models.py    -- Candidate (spec section 6.10's schema, plus
│   │                     file_size_bytes and imported_at -- see
│   │                     models.py's docstring for why those two are
│   │                     additions, not literally in the worked example)
│   ├── schema.py     -- validate_candidate_schema(), including a
│   │                     sha256-hex-format check on every hash field
│   ├── intake.py       -- import_candidate(): reads real file size and
│   │                     sha256 hash from disk, hashes the prompt and
│   │                     every reference asset
│   ├── errors.py         -- CandidateIntakeError (DMFError)
│   └── ids.py              -- generate_candidate_id() + is_valid_*
└── tests/generation/        -- 29 tests, one file per module above
```

```python
from dreammusicforge.generation import import_candidate

candidate = import_candidate(
    render_task_id=render_task.id, provider="kling", model_version="kling-v1.6",
    file_path=Path("renders/CANDIDATE-021-B-003.mp4"), prompt=kling_package.prompt,
    imported_at="2026-08-05T12:00:00+00:00",
)
candidate.output_hash   # sha256 of the actual file bytes -- independently reproducible
candidate.prompt_hash   # sha256 of the exact prompt text that produced it
```

Traceability here means what it says: `output_hash` is `hashlib.sha256`
of the candidate file's real bytes (via `core/hashing.py`'s
`hash_file()`, same stdlib-only function Release 0.1 built), not a
value the caller supplies and this release trusts. `import_candidate()`
fails closed on a missing candidate or reference file -- a `Candidate`
whose hash can't be computed from a real file isn't traceable, so it's
never returned.

**Release 0.9 is the first release in this repository that depends on
an external binary rather than stdlib alone.** It adds `verification/`,
which shells out to `ffmpeg`/`ffprobe` to turn a rendered candidate
file into an objective technical report -- this release's acceptance
test (spec section 19): "objective technical report generated from
video files."

Why the dependency: Release 0.2's `music/wav_inspector.py` reads WAV
files with stdlib `wave` because PCM WAV headers are trivial to parse
by hand. There is no equivalent for the H.264-encoded video and
AAC-encoded audio this release has to inspect -- Python's stdlib has no
video or compressed-audio codec, and writing one is not in scope for a
single release. `ffmpeg`/`ffprobe` were confirmed present in this
environment and are the same tool already proven, in the sibling
`agentic-twin` repository's own DreamMusicForge session, for exactly
this kind of real diagnostic (`volumedetect`/`astats`/`silencedetect`).

```
dreammusicforge/
├── verification/
│   ├── models.py        -- MediaMetadata, DurationFrameRateCheck,
│   │                         AudioRmsReport, SeamComparison,
│   │                         ColorShiftReport, TechnicalReport
│   ├── schema.py          -- dict-shaped schemas + validate_*_schema()
│   ├── ffmpeg_runner.py     -- the ONE module that invokes ffmpeg/
│   │                         ffprobe; every function builds its own
│   │                         fixed argv from typed parameters, never
│   │                         shell=True, never a caller-supplied
│   │                         command string -- see its module
│   │                         docstring for why that structural
│   │                         narrowness *is* spec rule 18's "media
│   │                         commands allowlisted"
│   ├── inspector.py          -- inspect_media(): duration, frame rate,
│   │                         resolution, codec, audio presence
│   ├── frames.py               -- extract_frame(): a real decoded
│   │                         still frame from a real timestamp
│   ├── seam.py                  -- compare_seam(): SSIM between two
│   │                         frames (spec 9.2's boundary check)
│   ├── audio.py                  -- measure_audio_rms(): real RMS/peak
│   │                         via ffmpeg's astats filter
│   ├── color.py                   -- measure_color_shift(): YUV
│   │                         average difference via signalstats
│   ├── errors.py                   -- FfmpegNotAvailableError,
│   │                         FfmpegRunError, TechnicalVerificationError
│   └── report.py                    -- generate_technical_report():
│                                    the orchestration
└── tests/verification/                -- 56 tests. Needs `-t .` on the
                                       discover command below, since
                                       fixtures.py uses a relative
                                       import other test packages in
                                       this repo don't need
```

```python
from dreammusicforge.verification import generate_technical_report

report = generate_technical_report(
    candidate_id=candidate.id, file_path=Path(candidate.file),
    expected_duration_seconds=render_task.duration_seconds, expected_frame_rate=24.0,
    previous_end_frame_path=previous_shots_last_frame,  # optional -- enables seam + color checks
    frame_extraction_dir=Path("scratch/frames"),
)

report.passed     # bool
report.failures   # e.g. ("audio: silent (RMS level -85.2 dB)",) -- human-readable, not just a score
```

Every number in a `TechnicalReport` is measured from the real file via
one of the wrappers above, never asserted. `measure_audio_rms()` in
particular generalizes the exact class of diagnostic (silent audio in a
rendered clip, detected via `astats`' RMS level) that a real debugging
session in the sibling `agentic-twin` repository used to root-cause a
genuine "no audio in the stitched video" bug -- see `verification/
audio.py`'s module docstring. `SSIM_SIMILARITY_THRESHOLD` (0.85),
`SILENCE_RMS_THRESHOLD_DB` (-60), and `COLOR_SHIFT_THRESHOLD` (10.0) are
this release's own thresholds, not spec-given numbers -- the spec
requires each check exist, not a specific cutoff.

Release 0.10 adds `repair/`, which turns a Release 0.9 `TechnicalReport`
into an accept/reject decision and -- for a rejected candidate -- a
bounded repair plan. This release's acceptance test (spec section 19):
"failed candidate produces a bounded repair plan." It's grounded in a
real failure, not a synthetic one: the user uploaded two actual Kling
AI 3.0 clips meant to be visually identical (same performer, same
costume, same hair, same stage) that weren't -- running Release 0.9's
real seam comparison against them measured SSIM 0.674, and this
release's default `continuity` threshold (70.0 on a 0-100 scale) is set
so that exact real number correctly triggers a reject. See
`repair/classifier.py`'s test suite, which uses those real measured
numbers directly rather than a made-up example.

```
dreammusicforge/
├── repair/
│   ├── models.py    -- Defect (spec section 8.9's schema), RepairPlan
│   │                     and VerificationResult (spec section 6.11's
│   │                     schema)
│   ├── schema.py     -- dict-shaped schemas + validate_*_schema(),
│   │                     including cross-field rules (reject requires
│   │                     a repair plan and at least one critical
│   │                     failure; accept requires neither)
│   ├── scoring.py      -- score_technical_report(): turns a Release
│   │                     0.9 TechnicalReport into the automated half
│   │                     of section 6.11's metrics dict (duration_
│   │                     frame_rate, audio, continuity, color_continuity)
│   ├── classifier.py    -- DEFAULT_CRITICAL_THRESHOLDS,
│   │                     METRIC_RECOMMENDATIONS, classify_failures()
│   ├── errors.py          -- AcceptanceRepairError (DMFError)
│   └── builder.py          -- build_repair_plan(), evaluate_candidate()
│                            -- the accept/reject workflow
└── tests/repair/            -- 57 tests, one file per module above
```

```python
from dreammusicforge.repair import score_technical_report, evaluate_candidate

metrics = score_technical_report(technical_report)  # from Release 0.9
result = evaluate_candidate(candidate_id=candidate.id, shot_id=shot.id, metrics=metrics)

result.decision          # "accept" or "reject"
result.repair.action     # e.g. "regenerate" -- present only when rejected
result.repair.preserve   # metrics that passed and must not be touched during repair
```

Section 6.11's own worked example doesn't just show generic actions --
it repairs a `lip_sync` failure with `dedicated_lip_sync_pass`, a name
that isn't in section 8.9's six-action list at all. `METRIC_RECOMMENDATIONS`
reuses that exact mapping for `lip_sync` rather than forcing every
failure through the generic vocabulary; `REPAIR_ACTIONS` is seeded from
section 8.9 but isn't schema-enforced as a closed list, since the spec's
own two examples don't agree on one. A rejected candidate with more than
one defect -- or any single defect whose top recommendation is itself
`regenerate` -- collapses to one `regenerate` action rather than several
partial fixes attempted at once; that's what "bounded" means here: one
shot, one action, an explicit `preserve` list naming what must survive.

The six metrics section 6.11's example shows beyond what this release
can compute automatically (`identity`, `hair`, `costume`, `world`,
`camera`, `lip_sync`) are intentionally not fabricated by
`score_technical_report()` -- spec section 9.3 explicitly defers those
to "adapter interfaces and manual scoring" until real models exist.
`evaluate_candidate()`'s `metrics` parameter accepts them the moment a
caller supplies them (manually, or from a future adapter) -- the
threshold/classification/repair machinery already works for any named
metric, not just the four this release measures itself.

Release 0.11 adds `assembly/`, which turns a set of accepted candidates
into one finished video with the canonical master song as its audio
track. This release's acceptance test (spec section 19): "accepted
shots assemble into one video with uninterrupted song."

```
dreammusicforge/
├── assembly/
│   ├── models.py    -- Transition (spec section 8.6's schema),
│   │                     AssembledClip, ExportManifest
│   ├── schema.py     -- dict-shaped schemas + validate_*_schema(),
│   │                     including an overlap check across the final
│   │                     timeline
│   ├── ffmpeg_runner.py -- the one module that invokes ffmpeg for this
│   │                     package (normalize / concat / mux), each
│   │                     function building its own fixed argv, same
│   │                     allowlisting discipline as Release 0.9's
│   │                     verification/ffmpeg_runner.py -- a separate
│   │                     copy, not a shared import, since the two
│   │                     packages invoke ffmpeg for different purposes
│   ├── pipeline.py       -- normalize_clip(), concatenate_clips(),
│   │                     concatenate_clips_with_transitions(),
│   │                     replace_audio() -- thin typed wrappers
│   ├── errors.py           -- AssemblyError (DMFError)
│   └── builder.py           -- assemble_film(): the orchestration
└── tests/assembly/            -- 39 tests, one file per module above
    (needs ffmpeg on PATH)
```

```python
from dreammusicforge.assembly import assemble_film

manifest = assemble_film(
    master_song=master_song,                                    # Release 0.2
    accepted=((candidate_a, result_a), (candidate_b, result_b)), # Releases 0.8 + 0.10, decision == "accept"
    shots_by_candidate_id={candidate_a.id: shot_a, candidate_b.id: shot_b},
    output_width=1080, output_height=1920, output_frame_rate=30.0,
    work_dir=Path("scratch/assembly"), output_path=Path("final.mp4"),
    created_at="2026-08-05T00:00:00+00:00",
)
manifest.output_hash            # sha256 of the real final file
manifest.total_duration_seconds
```

The audio in the final file is **never** a concatenation of each clip's
own audio track -- it's one continuous pull from the master song file,
replacing whatever audio the individual Kling candidates carried
entirely (spec Law 3.9, "master audio remains external"; Law 3.2,
"music is the master clock"). That's a deliberate departure from how
the two real reference stitch files this session reviewed were built
(each concatenated its clips' own audio, which resets or jumps at every
cut) -- `replace_audio()` fixes that structurally rather than leaving it
to chance.

`assemble_film()` fails closed on three things a caller might get
wrong: a candidate whose `VerificationResult.decision` isn't `"accept"`
(Release 0.10) never reaches ffmpeg; a `VerificationResult` that doesn't
actually belong to the candidate it's paired with is rejected the same
way; and a requested `Transition` whose type isn't one this release
actually executes raises rather than silently falling back to a hard
cut without saying so. Of spec section 8.6's ten named transition types,
only `hard_cut` is executed -- the other nine (dissolve, dip to black,
foreground wipe, ...) need real compositing this repository doesn't
have yet. That's not a gap invented for convenience: this session's own
real reference video (a professionally produced ~4-minute music video
reviewed earlier) used exactly this technique -- hard cuts between
fully distinct scenes, no attempt to bridge them -- to move between
its chapters, which is also the strategy this session settled on for
handling Kling's identity/costume/world drift across separately
generated clips. `hard_cut` being the one implemented type isn't a
placeholder; it's the one this pipeline's own real evidence says is
load-bearing.

One real bug surfaced by running this against two differently-sourced
real-shaped clips (not caught by any unit test in isolation): scaling
two clips to identical pixel dimensions isn't enough for ffmpeg's
concat filter to accept them if their sources had different sample
aspect ratios -- `normalize_clip()` now forces `setsar=1` explicitly.
`tests/assembly/test_pipeline.py`'s
`test_joins_clips_with_originally_different_aspect_ratios` is the
regression test for it.

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
  discover -s dreammusicforge/tests/genome` (67 tests), `python -m
  unittest discover -s dreammusicforge/tests/production` (64 tests),
  `python -m unittest discover -s dreammusicforge/tests/capability_atlas`
  (47 tests), `python -m unittest discover -s
  dreammusicforge/tests/slicer` (57 tests), `python -m unittest discover
  -s dreammusicforge/tests/providers/kling` (29 tests), `python -m
  unittest discover -s dreammusicforge/tests/generation` (29 tests),
  `python -m unittest discover -s dreammusicforge/tests/verification -t .`
  (56 tests -- needs `-t .`, see below, and needs ffmpeg/ffprobe on
  PATH), `python -m unittest discover -s dreammusicforge/tests/repair`
  (57 tests), `python -m unittest discover -s
  dreammusicforge/tests/assembly -t .` (39 tests -- also needs `-t .`
  and ffmpeg on PATH), and `python -m dreammusicforge.apps.cli.main`
  from the repository root -- none require a pip install step.
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

Renderer Capability Atlas (0.5), Video Slicer (0.6), provider compilers
(0.7+), verification, repair, assembly, and the Operator Studio web
interface (0.15) remain unbuilt, per the spec's own phased plan -- none
of that is stubbed out here, per the spec's own rule against labeling
provisional logic as production logic.

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
generated asset actually honors a declared invariant. Release 0.4 adds
structural shot-to-shot continuity checking (state chaining), but it
still isn't tied back to `FilmGenome.invariants` by name -- that linkage,
and checking a *generated asset* against either, is verification-stage
work (spec pipeline diagram, section 2), still not built.

### What Release 0.4 deliberately does not include

No `renderer_risk`, `slice_strategy`, `slices`, or `editing` on `Shot`,
even though spec section 6.8's worked example shows all of them on one
`shot` object -- those are Video Slicer (0.6) outputs that come after
Production Graph compilation in the pipeline (spec section 2). Building
them here would mean claiming a later release's integration before that
release exists; see `production/models.py`'s module docstring for the
same point made in more detail.

No cross-check between a `Shot.timing.lyric_ids` and an actual
`Timeline` (Release 0.2) -- `lyric_ids` is validated for shape (a list of
non-empty strings) but not for whether each id resolves to a real
`LyricLine`. Wiring `production/builder.py` to accept a `Timeline`
alongside the `FilmGenome` it already takes would close this the same
way `assemble_production_graph()` already closes the performer/costume/
world case; it just wasn't done in this pass, to keep the release's
diff to one new cross-package integration point (genome) rather than
two (genome and music) at once.

No `Project` integration: `Project.production_graph_id` (added in
Release 0.1) is still an unresolved forward reference, same gap as
`film_genome_id` in Release 0.3. No persistence layer or CLI either --
`Sequence`, `SemanticEvent`, `Shot`, and `ProductionGraph` exist only as
in-memory dataclasses returned by `production/builder.py`.

The same-sequence, same-performer scope for state-chaining is this
release's own interpretation, not something spec section 19's terse
"dependencies; transition relationships" bullet points spell out
precisely. A chain is enforced only between shots that share both a
`sequence_id` and a `requirements.performer_id` -- two shots featuring
different performers, or shots in different sequences, are not required
to chain state. This was chosen because nothing in the spec text
describes a *global*, cross-performer, cross-sequence state machine, and
this same repository's pre-spec `runtime.py` scopes its own equivalent
check to one continuous clip-to-clip chain, not an ensemble-wide one.
Worth revisiting if a later release's requirements need a different
scope.

### What Release 0.5 deliberately does not include

No risk analysis or strategy selection -- `evaluate_shot_fit()`'s hard
disqualifiers cover only the fields already on `ShotRequirements`
(duration, character count, camera motion, lip sync); the fuller
`risk_factors` vocabulary in spec section 7.3 (`identity_precision`,
`prop_interaction`, `hand_complexity`, `transition_complexity`, and so
on) and the five-way strategy selection (Direct Render / Controlled
Continuation / Layered Compositing / Editorial Illusion / External
Production Required) in section 7.4 are Video Slicer (0.6) work, not
this release's. This release answers "which provider fits this shot,"
not "how should this shot be broken into renderable pieces."

No named-capability vocabulary is fixed or validated against a closed
list. A capability's `name` can be any non-empty string; this release
doesn't require providers to declare capabilities under a specific set
of names, or cross-check that every name a shot's `acceptance` dict
uses is one every profile recognizes. Score aggregation in
`evaluate_shot_fit()` handles a missing name by scoring it 0.0, which
is deliberately how an unrecognized or not-yet-declared capability name
is meant to behave -- but there's no separate report of "this profile
doesn't know about the capability names this project uses," which could
be a useful addition later.

No persistence layer or CLI, same gap as every release since 0.2:
`RendererCapabilityProfile` and `ProviderFitReport` exist only as
in-memory dataclasses. No `Project` integration either -- nothing here
is wired to a `Project`, since the spec doesn't give `Project` a
capability-atlas-shaped forward reference the way it does for
`master_song_id`/`film_genome_id`/`production_graph_id`.

### What Release 0.6 deliberately does not include

`editorial_illusion` is never auto-selected -- see the walkthrough above
and `slicer/strategy.py`'s module docstring for why: it requires a
creative/symbolic judgment call this system has no way to make. A
future release could add it once there's an actual creative-review input
(a human decision, or some other real signal) to drive the choice; until
then, shots that might suit it fall through to whichever of the other
four strategies the deterministic rules produce.

`layered_compositing`'s visual layers are deliberately coarse: always
`world_pass` and `performer_pass`, plus `lip_sync_pass` when required --
not the finer per-character layers spec section 6.8's worked example
shows (`dancers_left`, `dancers_right`). Producing those would need
choreography/blocking data (who stands where, which characters group
together) that isn't in the `Shot` model this release has to work with;
inventing plausible-sounding layer names without that data would be
exactly the kind of fabrication section 22 forbids. `motion_layers`
is similarly minimal -- one `primary_motion` layer per shot, because
`camera_motion` is the only motion-related field `ShotRequirements`
carries.

`RenderTask.mode`, `.prompt_file`, and `.negative_prompt_file` are
always `None` in this release's output, even though spec section 6.9's
`render_task` YAML shows all three populated. Section 19 names "mode
selection" and "prompt generation" as explicit Release 0.7 (Kling
Compiler) deliverables; populating them here would mean claiming a
later release's integration before it exists (spec section 22, rule 14).

No fallback planning beyond `external_production_required`. Spec section
19 lists "fallback planning" as its own deliverable, and this release
covers the one case that's unambiguous from the data available (no
provider can render the shot at all) with a `FallbackPlan`. A richer
fallback system -- e.g. re-attempting with a relaxed strategy after a
render fails verification -- needs Release 0.9-0.10's verification and
repair machinery to have something concrete to react to; it doesn't
exist yet.

No persistence layer or CLI, and no `Project` integration, same pattern
as every release since 0.2: `SliceResult` and everything inside it exist
only as in-memory dataclasses returned by `slicer/builder.py`.

### What Release 0.7 deliberately does not include

No actual Kling API call. `compile_kling_package()` produces the
package -- prompt, negative prompt, mode, reference manifest, duration
check -- entirely offline; nothing in this release submits it anywhere,
polls a job, or downloads a result. That's Release 0.8 (Candidate Intake
and Evidence) and beyond, and it's also exactly the kind of "claim an
integration that was not executed" spec section 22's rule 14 forbids --
this release only compiles the request, it doesn't send it.

No `providers.base.VideoRenderer` interface (spec section 14). No
release has named it as a required deliverable yet, and implementing
it now would mean inventing `ProviderRequest`/`ProviderJob`/
`ProviderJobStatus`/`RenderedAsset` shapes with no spec example or
concrete caller to ground them in -- speculative scaffolding this
session has avoided everywhere else, and section 22 explicitly forbids
placeholder implementations labeled complete. `providers/kling/` stands
on its own as a set of plain functions rather than implementing an
unbuilt interface.

`KLING_MODES` (`text_to_video`, `image_to_video`, `start_end_frame`,
`video_extension`) is this release's own list. The spec shows one mode
in its section 6.9 example (`image_to_video`) and doesn't give a closed
vocabulary; the other three are standard, widely-documented Kling
capability names, not a verified account of what a specific Kling API
version supports. `KlingProfile.supported_modes` exists precisely so a
real deployment can narrow (or correct) this list without changing code.

No file I/O. `KlingPackage.prompt` and `.negative_prompt` hold generated
text directly, not file paths (`prompts/RENDER-021-B.txt`, as spec
section 6.9 shows) -- writing prompt files is a decision this release
leaves to the caller, consistent with the rest of this repository never
performing filesystem writes outside `storage/sqlite_repository.py`
(Release 0.1) and the CLI's own explicit `project init` command.

No persistence layer, CLI, or `Project` integration -- same pattern as
every release since 0.2.

### What Release 0.8 deliberately does not include

No media inspection. `Candidate.file_size_bytes` is filesystem metadata
(`Path.stat().st_size`) only -- nothing here opens the video file,
reads its duration, resolution, frame rate, or codec, or checks that it
is in fact a valid video file at all. Section 19 names "media
inspection" as Release 0.9's own deliverable ("Technical Verification"),
and section 6.10's `candidate` schema itself has no stream-level fields
-- adding them here would mean claiming a later release's integration.

No verification. `verification_status` and `decision` both default to
`"pending"` on import and stay there -- nothing in this release scores,
accepts, or rejects a candidate. That's exactly spec Law 3.6
("verification before canon"): a freshly imported candidate has no
canonical standing yet, and Release 0.9's media inspection plus later
releases' identity/costume/world/lip-sync checks (section 6.11's
`verification_result`) are what would move it out of `"pending"`.

`CANDIDATE_VERIFICATION_STATUSES` and `CANDIDATE_DECISIONS` are this
release's own enums inferred from spec section 6.10/6.11's example
values (`"pending"`, `"reject"`) -- the spec doesn't give a closed list
for either, so `"passed"`/`"failed"` and `"accept"`/`"reject"` are this
release's own naming choice, not a verified spec vocabulary.

No persistence layer or CLI -- `Candidate` exists only as an in-memory
dataclass returned by `generation/intake.py`, same pattern as every
release since 0.2. Nothing here writes an evidence record to disk or a
database either, even though "evidence" is half of this release's own
name -- the *evidence* this release produces is the Candidate's own
hash fields, verifiable against the file on disk at any time; a durable,
queryable evidence ledger (spec section 8.12's "evidence and versioning
service") is later work.

### What Release 0.9 deliberately does not include

No identity, boundary-beyond-seam, or semantic checks. Spec section
9.1's "Technical checks" list is what this release covers (file
readable, duration, frame rate, resolution, codec, audio presence,
silence, loudness) plus the seam/color piece of section 9.2's boundary
checks. Section 9.2's other boundary checks (subject scale, pose
difference, motion-vector difference), section 9.3's identity checks
(face embedding similarity, costume feature matching), and section
9.5's semantic checks (human review, confidence, pass/fail) all need
either a trained model, a human reviewer, or both -- none of that
exists in this repository, and faking a score for any of them would be
exactly the placeholder logic spec section 22 forbids. Section 9.1's
"black frames," "frozen frames," "dropped frames," and "clipping"
checks are also not built -- each needs its own ffmpeg filter
(`blackdetect`, `freezedetect`, a frame-count cross-check, and
`astats`' clip-count field respectively) and its own threshold
calibration; this release scoped to the checks spec section 19's own
"Build" list names explicitly (media inspection, frame extraction, seam
comparison, audio RMS, color shift, duration and frame-rate checks) and
left the rest of 9.1's longer list as a stated gap rather than rushing
partial coverage of all of it.

No acceptance decision. `TechnicalReport.passed` is this release's own
pass/fail roll-up of the checks it runs -- it is not spec section
6.11's `verification_result` (identity/hair/costume/world/camera/
lip_sync metrics, an overall score, a decision, a repair
recommendation), which needs the identity/boundary/semantic checks this
release doesn't have and is Release 0.10's job (Acceptance and Repair
Engine).

No `Candidate` integration. `generate_technical_report()` takes a
`candidate_id` and a `file` path as plain arguments, not a
`generation.Candidate` object -- wiring the two together (and writing
`verification_status` back onto the `Candidate`) is straightforward but
wasn't done here, to keep this release's diff scoped to what section 19
names.

No persistence layer or CLI, same pattern as every release since 0.2.

### What Release 0.10 deliberately does not include

No shot-selection ranking. Spec section 8.10 describes ranking multiple
candidates for the same shot against each other ("a beautiful candidate
with a critical continuity failure must rank below a less beautiful
candidate that preserves the canonical film") -- this release evaluates
one candidate at a time (`evaluate_candidate()`), producing an
accept/reject decision and a repair plan for it alone. Comparing several
candidates for the same shot and picking a winner is Release 0.10's
"accept/reject workflow" applied per-candidate, not the separate
ranking-across-candidates step 8.10 describes -- that's a defensible
reading of section 19's own Build list, which says "accept/reject
workflow," not "candidate ranking," but it's a real scope line worth
naming rather than leaving implicit.

No identity/hair/costume/world/camera/lip_sync metrics computed
automatically -- `score_technical_report()` produces only what Release
0.9 can measure (`duration_frame_rate`, `audio`, `continuity`,
`color_continuity`); the six qualitative metrics spec section 6.11's
own worked example shows need a trained model or a human reviewer this
repository doesn't have (section 9.3). `evaluate_candidate()`'s
`metrics` parameter is deliberately open to whatever a caller supplies,
so this isn't a hard wall, but nothing here computes those six on its
own.

No actual repair *execution*. A `RepairPlan` names an action
(`regenerate`, `dedicated_lip_sync_pass`, ...) and what to preserve --
nothing in this release re-prompts a provider, re-renders a shot, or
feeds a repair plan back into Release 0.6's slicer or Release 0.7's
Kling compiler to produce a new `RenderTask`/`KlingPackage`. That
closes-the-loop integration is real future work, not yet built.

No `Candidate` integration -- same gap as Release 0.9: `evaluate_candidate()`
takes a `candidate_id` as a plain string, not a `generation.Candidate`
object, and nothing writes the resulting `decision` back onto a stored
`Candidate.decision`/`.verification_status` field (both would still
read `"pending"` from Release 0.8). No persistence layer or CLI either.

### What Release 0.11 deliberately does not include

Eight of spec section 8.6's ten transition types are declared and
schema-validated but never executed -- `dip_to_black`, `foreground_wipe`,
`motion_match`, `graphic_match`, `color_bridge`, `light_flash`,
`blur_transition`, and `beat_cut` all need real video compositing
(masking, timed graphic overlays, motion analysis) this repository
doesn't have yet. `assemble_film()` fails closed on them rather than
silently rendering a hard cut and calling it something else. Real
compositing work is Release 0.13's territory (Masking and Compositing)
and beyond. (`dissolve` was added to the executed set after Release
0.11 shipped -- see "Editorial chapters" below.)

No lip-sync application (Release 0.12), no color grading or final audio
mixing beyond the one master-song swap (Release 0.14) -- clips are
normalized to a common resolution and frame rate, nothing more.
`normalize_clip()` doesn't attempt any color, exposure, or white-balance
matching between clips from different generations, even though that's
part of what a real "finishing" pass would do.

No verification of the *assembled* output against the project's overall
target duration or the master song's actual runtime -- `assemble_film()`
produces whatever duration the accepted clips sum to; nothing checks
that against `Project.target_duration_seconds` (Release 0.1) or flags a
film that's running short or long relative to the song. That check
belongs with an `ExportManifest` a `Project` can be validated against,
which needs the `Project` integration this release (like every release
since 0.2) doesn't have.

No re-running Release 0.9's technical verification against the
*assembled* file itself -- only the individual candidates that went
into it were verified (Release 0.9/0.10, before assembly). The real
gap this closes was named honestly back in Release 0.8's section of
this README: per-candidate verification and final-delivery verification
are different checks, and this release only does the former's
consumer, not the latter's producer.

No persistence layer or CLI, same pattern as every release since 0.2.

## Editorial chapters: per-sequence camera/color language and a second executable transition

Added after Release 0.11, not part of the spec's original numbered
release plan -- prompted by reviewing a real, professionally-produced
reference video in this session and extracting general editorial
technique from it (structure and pacing only, not its specific
content): the piece moves through distinct visual chapters, each with
its own camera vocabulary and color grading, and it relies on more than
hard cuts to move between them.

**Per-sequence camera/color language** (`production/models.py`,
`production/builder.py`). `Sequence` gained two optional fields,
`camera_language: CameraLanguage | None` and `color_language:
ColorLanguage | None`, defaulting to `None` -- "use the film's default."
`FilmGenome.camera_language`/`.color_language` (spec section 6.3's
shape) are unchanged and still the film-wide baseline. A sequence that
wants to look or move differently from the rest of the film -- a
chapter change -- declares its own; `production.resolve_camera_language(
sequence, film_genome)` / `resolve_color_language(sequence, film_genome)`
return the override if present, otherwise the film's default. Nothing
before this release could express "this chapter looks different," even
though every FilmGenome already has the vocabulary (`CameraLanguage`,
`ColorLanguage`) to describe how.

**`dissolve` is now executed** (`assembly/models.py`,
`assembly/ffmpeg_runner.py`, `assembly/pipeline.py`,
`assembly/builder.py`). `EXECUTABLE_TRANSITION_TYPES` grew from
`("hard_cut",)` to `("hard_cut", "dissolve")` -- the one other transition
in spec section 8.6's list that needs no additional compositing input
beyond the two adjacent clips themselves. `assemble_film()` now resolves
one `(transition_type, duration_seconds)` per adjacent shot pair in the
final chronological order (defaulting to an implicit hard cut when the
caller declares no `Transition` for that pair, so every existing caller
that never passes `transitions` is unaffected), validates that a
declared `Transition` actually corresponds to an adjacent pair and that
a dissolve's `duration_seconds` fits inside both of its neighboring
clips, and picks the ffmpeg path accordingly: a pure hard-cut sequence
still calls the original, unchanged `concatenate_clips()`; anything with
at least one dissolve calls the new `concatenate_clips_with_transitions()`,
which builds a mixed `concat`/`xfade` filter chain that can combine both
styles across an arbitrary number of clips, not just two.

A crossfade makes its two adjacent clips overlap in the final timeline
by design -- that's what a dissolve *is* -- so `AssembledClip.
start_seconds_in_final` bookkeeping and `assembly/schema.py`'s
overlap check both had to change: the schema now permits exactly the
overlap a declared dissolve transition explains (within a 0.5s
tolerance for ffmpeg re-encode drift) and still rejects anything else.

**A real ffmpeg bug found by actually running a 3-clip mixed chain**,
not by unit-testing `xfade` in isolation: ffmpeg's `concat` filter
output carries a different internal timebase than a raw decoded input,
and `xfade` refuses to run when its two inputs don't share one
("First input link main timebase ... do not match the corresponding
second input link xfade timebase"). Fixed by passing every stream --
both raw inputs and `concat` outputs -- through an explicit `fps=`
filter before it can reach an `xfade` node, which resets it to one
known, constant timebase. `tests/assembly/test_pipeline.py`'s
`test_three_clip_chain_mixes_hard_cut_and_dissolve` is the regression
test.

### What this deliberately does not include

The other eight named transition types (`dip_to_black`,
`foreground_wipe`, `motion_match`, `graphic_match`, `color_bridge`,
`light_flash`, `blur_transition`, `beat_cut`) still fail closed --
`dissolve` was the only one that needed no additional compositing input
beyond the two clips already being assembled. No ensemble/multi-performer
identity locking -- everything this session has actually run end to end
(hope, burgundy, rooftop) is a single performer; a real
multiple-dancers-on-stage sequence is untested ground and a harder
version of the same identity-drift problem `repair/` already handles
for one performer at a time. No genome-level validation that a
sequence's override and the film's default share any relationship
(e.g. a shared lens) -- a sequence can currently declare a wildly
inconsistent camera language from its film with no warning; that's a
deliberate choice (chapters *should* be allowed to look different) but
means this doesn't catch an override that's a typo rather than an
intentional chapter change.

## The original, pre-spec governed baseline

`runtime.py` and `dmf_ir/` predate this specification and are unrelated
to it -- see `TESTING.md` for their own test instructions. Nothing in
Release 0.1, Release 0.2, Release 0.3, Release 0.4, Release 0.5, Release 0.6, Release 0.7, Release 0.8, Release 0.9, Release 0.10, or Release 0.11 imports from, depends on, or
modifies either.
