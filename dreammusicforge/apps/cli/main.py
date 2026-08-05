"""CLI skeleton -- Release 0.1 implements exactly the subset of section 11's
command surface this release's domain object (Project) supports: init,
validate, and show (covering "created, saved, loaded, validated" from the
release's own acceptance criteria; save is implicit in init, since a
freshly created project is immediately persisted).

argparse, not click/typer: stdlib-only, consistent with every other module
in this repository having zero third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from ...core.errors import DMFError, ProjectValidationError
from ...core.ids import generate_project_id, is_valid_project_id, validate_project_id
from ...core.models import PROJECT_STATUSES, Project
from ...core.paths import confine_path
from ...core.schema import validate_project_schema
from ...storage.sqlite_repository import ProjectRepository

DEFAULT_DB_RELATIVE_PATH = ".dreammusicforge/kernel.db"
PROJECT_JSON_FILENAME = "project.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db_path_for_workspace(workspace: Path) -> Path:
    return confine_path(workspace, DEFAULT_DB_RELATIVE_PATH)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dmf", description="DreamMusicForge Film Compiler CLI")
    subparsers = parser.add_subparsers(dest="noun", required=True)

    project_parser = subparsers.add_parser("project", help="Project lifecycle commands")
    project_subparsers = project_parser.add_subparsers(dest="verb", required=True)

    init_parser = project_subparsers.add_parser("init", help="Create and persist a new project")
    init_parser.add_argument("title", help="Project title")
    init_parser.add_argument("--id", default=None, help="Explicit project id (default: auto-generated)")
    init_parser.add_argument("--workspace", default=".", help="Workspace directory (default: current directory)")
    init_parser.add_argument("--aspect-ratio", default="16:9")
    init_parser.add_argument("--resolution", default="1920x1080")
    init_parser.add_argument("--frame-rate", type=float, default=30)
    init_parser.add_argument("--target-duration-seconds", type=float, default=240)
    init_parser.add_argument("--provider", dest="providers", action="append", default=None, help="Repeatable: --provider kling --provider veo")
    init_parser.set_defaults(func=_cmd_init)

    validate_parser = project_subparsers.add_parser("validate", help="Validate a project JSON file")
    validate_parser.add_argument("path", help="Path to a project.json file")
    validate_parser.set_defaults(func=_cmd_validate)

    show_parser = project_subparsers.add_parser("show", help="Load and print a project by id")
    show_parser.add_argument("id", help="Project id")
    show_parser.add_argument("--workspace", default=".", help="Workspace directory (default: current directory)")
    show_parser.set_defaults(func=_cmd_show)

    return parser


def _cmd_init(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    project_id = args.id or generate_project_id()
    validate_project_id(project_id)

    now = _now_iso()
    project = Project(
        id=project_id,
        title=args.title,
        version="0.1.0",
        status="draft",
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
        frame_rate=args.frame_rate,
        target_duration_seconds=args.target_duration_seconds,
        providers=tuple(args.providers or []),
        created_at=now,
        updated_at=now,
    )

    errors = validate_project_schema(project.to_dict())
    if errors:
        raise ProjectValidationError(errors)

    db_path = _db_path_for_workspace(workspace)
    with ProjectRepository(db_path) as repo:
        repo.create(project)

    project_json_path = confine_path(workspace, PROJECT_JSON_FILENAME)
    project_json_path.write_text(json.dumps(project.to_dict(), indent=2) + "\n", encoding="utf-8")

    print(json.dumps(project.to_dict(), indent=2))
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.is_file():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: {path} is not valid JSON: {exc}", file=sys.stderr)
        return 1

    errors = validate_project_schema(data)
    project_id = data.get("id") if isinstance(data, dict) else None
    if isinstance(project_id, str) and not is_valid_project_id(project_id):
        errors.append(f"id {project_id!r} is not a valid project id (expected DMF-PROJECT-<hex>)")

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print("valid")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    db_path = _db_path_for_workspace(workspace)
    with ProjectRepository(db_path) as repo:
        project = repo.get(args.id)
    print(json.dumps(project.to_dict(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except DMFError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
