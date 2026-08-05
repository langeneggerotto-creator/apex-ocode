"""Typed Project model -- the kernel's one domain object for Release 0.1.
Everything else in the full spec (Film Genome, Production Graph, Master
Song, ...) is out of scope for this release; Project carries id-shaped
references to those (master_song_id, film_genome_id,
production_graph_id) that later releases will populate and resolve.

Deliberately a plain dataclass, not the JSON-Schema-in-a-dict pattern used
elsewhere in this repo's sibling dreammusicforge module: this is an
application with a real typed domain layer (per spec section 5's
core/models/ directory and section 22's "use typed Python"), not a
schema-validator pair. core/schema.py is the schema-shaped structural
contract that raw dict input is checked against before being parsed into
this type.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PROJECT_STATUSES = {"draft", "compiling", "rendering", "review", "complete", "archived"}


@dataclass(frozen=True)
class Project:
    id: str
    title: str
    version: str
    status: str
    aspect_ratio: str
    resolution: str
    frame_rate: int
    target_duration_seconds: float
    created_at: str
    updated_at: str
    providers: tuple[str, ...] = field(default_factory=tuple)
    master_song_id: str | None = None
    film_genome_id: str | None = None
    production_graph_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "version": self.version,
            "status": self.status,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "frame_rate": self.frame_rate,
            "target_duration_seconds": self.target_duration_seconds,
            "providers": list(self.providers),
            "master_song_id": self.master_song_id,
            "film_genome_id": self.film_genome_id,
            "production_graph_id": self.production_graph_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "Project":
        """Assumes data already passed core.schema.validate_project_schema
        -- does not re-check required fields itself, same discipline as
        the sibling dreammusicforge schema modules' parse_*() functions."""
        return Project(
            id=data["id"],
            title=data["title"],
            version=data["version"],
            status=data["status"],
            aspect_ratio=data["aspect_ratio"],
            resolution=data["resolution"],
            frame_rate=int(data["frame_rate"]),
            target_duration_seconds=float(data["target_duration_seconds"]),
            providers=tuple(data.get("providers", [])),
            master_song_id=data.get("master_song_id"),
            film_genome_id=data.get("film_genome_id"),
            production_graph_id=data.get("production_graph_id"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def with_updated_timestamp(self, updated_at: str) -> "Project":
        """Projects are frozen (immutable) -- every mutation is an
        explicit new value, never an in-place field assignment."""
        data = self.to_dict()
        data["updated_at"] = updated_at
        return Project.from_dict(data)
