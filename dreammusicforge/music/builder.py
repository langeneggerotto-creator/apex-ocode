"""Assembly helpers: the functions that turn a WAV file plus a few
human-supplied facts (bpm, time signature, section/lyric boundaries) into
the canonical Timeline this release's acceptance test names -- "one song
can become a canonical timeline" (spec section 19).

Every function here validates its own output against music/schema.py
before returning it, so a caller can never hold a MasterSong or Timeline
that wouldn't itself pass validation -- fail closed, same discipline as
storage/sqlite_repository.py's ProjectRepository.
"""
from __future__ import annotations

from pathlib import Path

from ..core.hashing import hash_file
from .beats import generate_beats
from .errors import TimelineValidationError
from .ids import generate_audio_id
from .models import Beat, LyricLine, MasterSong, Section, Timeline
from .schema import validate_master_song_schema, validate_timeline_schema
from .wav_inspector import inspect_wav


def build_master_song(
    source_file: Path,
    bpm: float,
    time_signature: str,
    song_id: str | None = None,
    stems: dict[str, str] | None = None,
) -> MasterSong:
    """Inspects source_file for real audio metadata (duration, sample
    rate, channels) and hashes its bytes; bpm and time_signature are
    declared inputs, not derived -- see music/models.py's module
    docstring for why."""
    metadata = inspect_wav(source_file)
    song = MasterSong(
        id=song_id or generate_audio_id(),
        source_file=str(source_file),
        duration_seconds=metadata.duration_seconds,
        sample_rate=metadata.sample_rate,
        channels=metadata.channels,
        bpm=bpm,
        time_signature=time_signature,
        hash=hash_file(source_file),
        stems=dict(stems or {}),
    )

    errors = validate_master_song_schema(song.to_dict())
    if errors:
        raise TimelineValidationError(errors)
    return song


def build_beats_for_song(
    master_song: MasterSong,
    beats_per_bar: int,
    offset_seconds: float = 0.0,
) -> tuple[Beat, ...]:
    """Thin wrapper over beats.generate_beats() that reads duration and
    bpm from an already-built MasterSong, so a caller assembling a
    Timeline doesn't have to repeat those two fields by hand."""
    return generate_beats(
        duration_seconds=master_song.duration_seconds,
        bpm=master_song.bpm,
        beats_per_bar=beats_per_bar,
        offset_seconds=offset_seconds,
    )


def assemble_timeline(
    master_song: MasterSong,
    sections: tuple[Section, ...] = (),
    beats: tuple[Beat, ...] = (),
    lyric_lines: tuple[LyricLine, ...] = (),
) -> Timeline:
    """Builds and validates a Timeline anchored to master_song.id.
    Raises TimelineValidationError (carrying every problem found) if the
    result would fail music.schema.validate_timeline_schema -- a caller
    never receives a Timeline that doesn't already pass validation."""
    timeline = Timeline(
        master_song_id=master_song.id,
        sections=tuple(sections),
        beats=tuple(beats),
        lyric_lines=tuple(lyric_lines),
    )

    errors = validate_timeline_schema(timeline.to_dict())
    if errors:
        raise TimelineValidationError(errors)
    return timeline
