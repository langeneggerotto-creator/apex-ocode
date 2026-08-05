from __future__ import annotations

import unittest

from dreammusicforge.core.models import PROJECT_STATUSES, Project

VALID_DATA = {
    "id": "DMF-PROJECT-deadbeef",
    "title": "Begin Again",
    "version": "0.1.0",
    "status": "draft",
    "aspect_ratio": "16:9",
    "resolution": "1920x1080",
    "frame_rate": 30,
    "target_duration_seconds": 240,
    "providers": ["kling", "veo"],
    "master_song_id": None,
    "film_genome_id": None,
    "production_graph_id": None,
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}


class ProjectRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        project = Project.from_dict(VALID_DATA)
        self.assertEqual(project.to_dict(), VALID_DATA)

    def test_providers_becomes_a_tuple(self):
        project = Project.from_dict(VALID_DATA)
        self.assertIsInstance(project.providers, tuple)
        self.assertEqual(project.providers, ("kling", "veo"))

    def test_missing_optional_ids_default_to_none(self):
        data = {k: v for k, v in VALID_DATA.items() if k not in ("master_song_id", "film_genome_id", "production_graph_id")}
        project = Project.from_dict(data)
        self.assertIsNone(project.master_song_id)
        self.assertIsNone(project.film_genome_id)
        self.assertIsNone(project.production_graph_id)


class ProjectImmutabilityTests(unittest.TestCase):
    def test_project_is_frozen(self):
        project = Project.from_dict(VALID_DATA)
        with self.assertRaises(Exception):
            project.title = "Changed"  # type: ignore[misc]

    def test_with_updated_timestamp_returns_new_instance(self):
        project = Project.from_dict(VALID_DATA)
        updated = project.with_updated_timestamp("2026-02-01T00:00:00+00:00")
        self.assertNotEqual(project.updated_at, updated.updated_at)
        self.assertEqual(project.updated_at, VALID_DATA["updated_at"])
        self.assertEqual(updated.updated_at, "2026-02-01T00:00:00+00:00")
        # everything else is unchanged
        self.assertEqual(updated.id, project.id)
        self.assertEqual(updated.title, project.title)


class ProjectStatusesTests(unittest.TestCase):
    def test_expected_statuses_present(self):
        self.assertEqual(PROJECT_STATUSES, {"draft", "compiling", "rendering", "review", "complete", "archived"})


if __name__ == "__main__":
    unittest.main()
