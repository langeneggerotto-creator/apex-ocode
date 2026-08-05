"""SQLite-backed Project repository -- the development-baseline storage
layer named in spec section 13.1. Stores each project as a JSON blob
(the canonical serialization) plus a handful of indexed columns for
lookup; the JSON blob, not the columns, is the source of truth for a
project's fields.

Every method that can fail does so with a typed error from core.errors,
never a bare sqlite3 exception leaking through -- callers should never
need to know this is SQLite underneath.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..core.errors import ProjectAlreadyExistsError, ProjectNotFoundError
from ..core.models import Project
from ..core.schema import validate_project_schema

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class ProjectRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute(_SCHEMA)
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "ProjectRepository":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def create(self, project: Project) -> Project:
        existing = self._connection.execute(
            "SELECT 1 FROM projects WHERE id = ?", (project.id,)
        ).fetchone()
        if existing is not None:
            raise ProjectAlreadyExistsError(project.id)

        self._insert_or_replace(project)
        return project

    def save(self, project: Project) -> Project:
        """Upsert -- unlike create(), does not require the project to be
        new. Used for both "update an existing project" and, internally,
        by create() after its own existence check."""
        self._insert_or_replace(project)
        return project

    def get(self, project_id: str) -> Project:
        row = self._connection.execute(
            "SELECT data FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if row is None:
            raise ProjectNotFoundError(project_id)
        return Project.from_dict(json.loads(row[0]))

    def list_projects(self) -> list[Project]:
        rows = self._connection.execute(
            "SELECT data FROM projects ORDER BY updated_at DESC"
        ).fetchall()
        return [Project.from_dict(json.loads(row[0])) for row in rows]

    def _insert_or_replace(self, project: Project) -> None:
        data = project.to_dict()
        errors = validate_project_schema(data)
        if errors:
            # Defensive: a Project constructed through normal code paths
            # should always be schema-valid already. This is not the place
            # to report validation errors to a user -- see
            # core.schema.validate_project_schema, called explicitly before
            # a Project is built from untrusted input (e.g. the CLI).
            raise AssertionError(f"refusing to persist a schema-invalid project: {errors}")

        self._connection.execute(
            "INSERT INTO projects (id, title, status, data, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "title=excluded.title, status=excluded.status, data=excluded.data, updated_at=excluded.updated_at",
            (project.id, project.title, project.status, json.dumps(data), project.created_at, project.updated_at),
        )
        self._connection.commit()
