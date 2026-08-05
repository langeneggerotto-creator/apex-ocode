# DreamMusicForge Film Compiler

Provider-neutral AI music-video production pipeline, governed as an APEX
OCode module (`governance/DELEGATION_CONTRACT.yaml`). Built from
`DREAMMUSICFORGE FILM COMPILER — Application Specification v1.0` in
independently testable, reviewable releases -- see the spec's section 19
phased plan. **This README describes only what is actually built.**

## What exists today: Release 0.1 — Project Kernel

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
  dreammusicforge/tests/kernel` and `python -m
  dreammusicforge.apps.cli.main` from the repository root -- both require
  no installation step.

### What Release 0.1 deliberately does not include

Everything past "create, save, load, validate one Project" is later
releases, per the spec's own phased plan: Master Song analysis (0.2),
Film Genome (0.3), Production Graph (0.4), Renderer Capability Atlas
(0.5), Video Slicer (0.6), provider compilers (0.7+), verification,
repair, assembly, and the Operator Studio web interface (0.15). None of
that is stubbed out here -- there are no placeholder modules for later
releases, per the spec's own rule against labeling provisional logic as
production logic.

## The original, pre-spec governed baseline

`runtime.py` and `dmf_ir/` predate this specification and are unrelated
to it -- see `TESTING.md` for their own test instructions. Nothing in
Release 0.1 imports from, depends on, or modifies either.
