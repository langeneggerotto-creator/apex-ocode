"""Typed domain model for Release 0.13 -- Masking and Compositing.

Not verified against the original spec's own section text for this
release (only the release name survived this session's context
compaction, same gap as Release 0.12 -- see lipsync/models.py's
docstring). This shape is this repository's own design: two named
`CompositeLayer`s (`"background"` and `"foreground"`) combined into one
`CompositeResult`, following the earlier-named "Layered Compositing"
and "Editorial Illusion" strategy names surfaced in Release 0.5's own
README section (spec section 7.4's five-way strategy vocabulary) --
this is the first release that actually executes either of them,
rather than only naming them as a `slicer/` strategy choice.

MASK_TYPES declares the vocabulary this release recognizes;
EXECUTABLE_MASK_TYPES is the subset actually run through ffmpeg --
`"chromakey"` (colorkey + overlay) and `"none"` (a plain opaque
overlay, no keying). `"alpha_channel"` (compositing against a source
that already carries a real alpha channel) is declared but not
executed, same fail-closed discipline `assembly/`'s
`EXECUTABLE_TRANSITION_TYPES` established for transitions it can't yet
run.
"""
from __future__ import annotations

from dataclasses import dataclass, field

LAYER_TYPES = ("background", "foreground")
MASK_TYPES = ("chromakey", "alpha_channel", "none")
EXECUTABLE_MASK_TYPES = ("chromakey", "none")


@dataclass(frozen=True)
class CompositeLayer:
    layer_type: str
    source_file: str
    mask_type: str = "none"
    chroma_color: str | None = None
    chroma_similarity: float = 0.3
    chroma_blend: float = 0.1

    def to_dict(self) -> dict:
        return {
            "layer_type": self.layer_type,
            "source_file": self.source_file,
            "mask_type": self.mask_type,
            "chroma_color": self.chroma_color,
            "chroma_similarity": self.chroma_similarity,
            "chroma_blend": self.chroma_blend,
        }

    @staticmethod
    def from_dict(data: dict) -> "CompositeLayer":
        return CompositeLayer(
            layer_type=data["layer_type"],
            source_file=data["source_file"],
            mask_type=data.get("mask_type", "none"),
            chroma_color=data.get("chroma_color"),
            chroma_similarity=float(data.get("chroma_similarity", 0.3)),
            chroma_blend=float(data.get("chroma_blend", 0.1)),
        )


@dataclass(frozen=True)
class CompositeResult:
    id: str
    shot_id: str
    output_file: str
    output_hash: str
    width: int
    height: int
    duration_seconds: float
    layers: tuple[CompositeLayer, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "shot_id": self.shot_id,
            "output_file": self.output_file,
            "output_hash": self.output_hash,
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "layers": [layer.to_dict() for layer in self.layers],
        }

    @staticmethod
    def from_dict(data: dict) -> "CompositeResult":
        return CompositeResult(
            id=data["id"],
            shot_id=data["shot_id"],
            output_file=data["output_file"],
            output_hash=data["output_hash"],
            width=int(data["width"]),
            height=int(data["height"]),
            duration_seconds=float(data["duration_seconds"]),
            layers=tuple(CompositeLayer.from_dict(item) for item in data.get("layers", [])),
        )
