"""Typed domain model for Release 0.3 -- "a complete Film Genome can be
created and validated" (spec section 19's acceptance test for this
release).

Field shapes follow spec section 6.3 (film_genome), 6.4 (performer), 6.5
(costume), and 6.6 (world) example YAML, field for field. Same
to_dict()/from_dict() convention as core/models.py's Project and
music/models.py's MasterSong -- frozen dataclasses, not the
JSON-Schema-in-a-dict pattern used elsewhere in this repo's sibling
dreammusicforge module.

FilmGenome.transformation_from/transformation_to are stored as two
separate fields rather than a `from`/`to` dict, because `from` is a
Python keyword; to_dict()/from_dict() still produce/accept the spec's
{"from": ..., "to": ...} shape.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Performer:
    id: str
    display_name: str
    reference_assets: tuple[str, ...]
    immutable: dict[str, str]
    mutable_by_contract: dict[str, str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "identity": {"reference_assets": list(self.reference_assets)},
            "immutable": dict(self.immutable),
            "mutable_by_contract": dict(self.mutable_by_contract),
        }

    @staticmethod
    def from_dict(data: dict) -> "Performer":
        identity = data.get("identity", {})
        return Performer(
            id=data["id"],
            display_name=data["display_name"],
            reference_assets=tuple(identity.get("reference_assets", [])),
            immutable=dict(data.get("immutable", {})),
            mutable_by_contract=dict(data.get("mutable_by_contract", {})),
        )


@dataclass(frozen=True)
class Costume:
    id: str
    topology: dict[str, str]
    material: str
    references: dict[str, str]
    embroidery: str | None = None
    accessories: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topology": dict(self.topology),
            "material": self.material,
            "embroidery": self.embroidery,
            "accessories": dict(self.accessories),
            "references": dict(self.references),
        }

    @staticmethod
    def from_dict(data: dict) -> "Costume":
        return Costume(
            id=data["id"],
            topology=dict(data.get("topology", {})),
            material=data["material"],
            embroidery=data.get("embroidery"),
            accessories=dict(data.get("accessories", {})),
            references=dict(data.get("references", {})),
        )


@dataclass(frozen=True)
class World:
    id: str
    type: str
    references: dict[str, str]
    geometry: str
    palette: str
    lighting: str
    atmosphere: str
    props: tuple[str, ...] = field(default_factory=tuple)
    allowed_transformations: tuple[str, ...] = field(default_factory=tuple)
    forbidden_transformations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "references": dict(self.references),
            "geometry": self.geometry,
            "palette": self.palette,
            "lighting": self.lighting,
            "atmosphere": self.atmosphere,
            "props": list(self.props),
            "allowed_transformations": list(self.allowed_transformations),
            "forbidden_transformations": list(self.forbidden_transformations),
        }

    @staticmethod
    def from_dict(data: dict) -> "World":
        return World(
            id=data["id"],
            type=data["type"],
            references=dict(data.get("references", {})),
            geometry=data["geometry"],
            palette=data["palette"],
            lighting=data["lighting"],
            atmosphere=data["atmosphere"],
            props=tuple(data.get("props", [])),
            allowed_transformations=tuple(data.get("allowed_transformations", [])),
            forbidden_transformations=tuple(data.get("forbidden_transformations", [])),
        )


@dataclass(frozen=True)
class CameraLanguage:
    lens_vocabulary: tuple[str, ...]
    movement_vocabulary: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "lens_vocabulary": list(self.lens_vocabulary),
            "movement_vocabulary": list(self.movement_vocabulary),
        }

    @staticmethod
    def from_dict(data: dict) -> "CameraLanguage":
        return CameraLanguage(
            lens_vocabulary=tuple(data.get("lens_vocabulary", [])),
            movement_vocabulary=tuple(data.get("movement_vocabulary", [])),
        )


@dataclass(frozen=True)
class ColorLanguage:
    opening: str
    development: str
    climax: str

    def to_dict(self) -> dict:
        return {"opening": self.opening, "development": self.development, "climax": self.climax}

    @staticmethod
    def from_dict(data: dict) -> "ColorLanguage":
        return ColorLanguage(
            opening=data["opening"], development=data["development"], climax=data["climax"],
        )


@dataclass(frozen=True)
class FilmGenome:
    id: str
    transformation_from: str
    transformation_to: str
    performer_ids: tuple[str, ...]
    costume_ids: tuple[str, ...]
    world_ids: tuple[str, ...]
    camera_language: CameraLanguage
    color_language: ColorLanguage
    motifs: tuple[str, ...]
    invariants: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "transformation": {"from": self.transformation_from, "to": self.transformation_to},
            "performer_ids": list(self.performer_ids),
            "costume_ids": list(self.costume_ids),
            "world_ids": list(self.world_ids),
            "camera_language": self.camera_language.to_dict(),
            "color_language": self.color_language.to_dict(),
            "motifs": list(self.motifs),
            "invariants": list(self.invariants),
        }

    @staticmethod
    def from_dict(data: dict) -> "FilmGenome":
        transformation = data.get("transformation", {})
        return FilmGenome(
            id=data["id"],
            transformation_from=transformation.get("from", ""),
            transformation_to=transformation.get("to", ""),
            performer_ids=tuple(data.get("performer_ids", [])),
            costume_ids=tuple(data.get("costume_ids", [])),
            world_ids=tuple(data.get("world_ids", [])),
            camera_language=CameraLanguage.from_dict(data.get("camera_language", {})),
            color_language=ColorLanguage.from_dict(data.get("color_language", {})),
            motifs=tuple(data.get("motifs", [])),
            invariants=tuple(data.get("invariants", [])),
        )
