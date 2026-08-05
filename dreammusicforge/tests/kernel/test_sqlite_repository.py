from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.core.errors import ProjectAlreadyExistsError, ProjectNotFoundError
from dreammusicforge.core.models import Project
from dreammusicforge.storage.sqlite_repository import ProjectRepository


def _make_project(project_id: str = "DMF-PROJECT-deadbeef", title: str = "Begin Again") -> Project:
    return Project(
        id=project_id, title=title, version="0.1.0", status="draft",
        aspect_ratio="16:9", resolution="1920x1080", frame_rate=30,
        target_duration_seconds=240, providers=("kling",),
        created_at="2026-01-01T00:00:00+00:00", updated_at="2026-01-01T00:00:00+00:00",
    )


class ProjectRepositoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "kernel.db"

    def tearDown(self):
        self._tmp.cleanup()

    def test_create_then_get_round_trips(self):
        with ProjectRepository(self.db_path) as repo:
            project = _make_project()
            repo.create(project)
            loaded = repo.get(project.id)
            self.assertEqual(loaded, project)

    def test_create_twice_with_same_id_raises(self):
        with ProjectRepository(self.db_path) as repo:
            project = _make_project()
            repo.create(project)
            with self.assertRaises(ProjectAlreadyExistsError):
                repo.create(project)

    def test_get_missing_project_raises(self):
        with ProjectRepository(self.db_path) as repo:
            with self.assertRaises(ProjectNotFoundError):
                repo.get("DMF-PROJECT-00000000")

    def test_save_updates_an_existing_project(self):
        with ProjectRepository(self.db_path) as repo:
            project = _make_project()
            repo.create(project)
            updated = project.with_updated_timestamp("2026-02-01T00:00:00+00:00")
            repo.save(updated)
            loaded = repo.get(project.id)
            self.assertEqual(loaded.updated_at, "2026-02-01T00:00:00+00:00")

    def test_save_can_create_a_new_project_too(self):
        with ProjectRepository(self.db_path) as repo:
            project = _make_project()
            repo.save(project)
            self.assertEqual(repo.get(project.id), project)

    def test_list_projects_returns_everything_created(self):
        with ProjectRepository(self.db_path) as repo:
            a = _make_project("DMF-PROJECT-aaaaaaaa", "Film A")
            b = _make_project("DMF-PROJECT-bbbbbbbb", "Film B")
            repo.create(a)
            repo.create(b)
            ids = {p.id for p in repo.list_projects()}
            self.assertEqual(ids, {a.id, b.id})

    def test_repository_persists_across_reconnection(self):
        project = _make_project()
        with ProjectRepository(self.db_path) as repo:
            repo.create(project)
        with ProjectRepository(self.db_path) as repo:
            self.assertEqual(repo.get(project.id), project)

    def test_db_parent_directory_is_created_if_missing(self):
        nested_db = Path(self._tmp.name) / "nested" / "dir" / "kernel.db"
        with ProjectRepository(nested_db) as repo:
            repo.create(_make_project())
        self.assertTrue(nested_db.is_file())


if __name__ == "__main__":
    unittest.main()
