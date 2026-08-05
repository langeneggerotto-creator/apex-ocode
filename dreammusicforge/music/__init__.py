"""DreamMusicForge Film Compiler -- music/timeline package (Release 0.2).

Public API:

    from dreammusicforge.music import (
        Beat, Section, LyricLine, MasterSong, Timeline, SECTION_TYPES,
        WavMetadata, inspect_wav,
        seconds_to_timecode, timecode_to_seconds, seconds_to_bar_beat,
        seconds_to_frame, frame_to_seconds,
        generate_beats,
        generate_audio_id, is_valid_audio_id,
        generate_section_id, is_valid_section_id,
        generate_lyric_id, is_valid_lyric_id,
        validate_master_song_schema, validate_timeline_schema,
        validate_section_schema, validate_beat_schema, validate_lyric_line_schema,
        MASTER_SONG_SCHEMA, MASTER_SONG_SCHEMA_VERSION,
        TIMELINE_SCHEMA_VERSION,
        build_master_song, build_beats_for_song, assemble_timeline,
        AudioInspectionError, InvalidTimecodeError, TimelineValidationError,
    )

Everything else in the full spec (Film Genome, Production Graph, slicer,
providers, verification, assembly, ...) is later releases and is not
present here. Release 0.1's core/ and storage/ packages are unmodified
except for core/ids.py, which gained generic generate_id()/is_valid_id()
helpers this package's ids.py builds on -- see core/ids.py's docstring.
"""
from __future__ import annotations

from .beats import generate_beats
from .builder import assemble_timeline, build_beats_for_song, build_master_song
from .errors import AudioInspectionError, InvalidTimecodeError, TimelineValidationError
from .frames import frame_to_seconds, seconds_to_frame
from .ids import (
    generate_audio_id, generate_lyric_id, generate_section_id, is_valid_audio_id,
    is_valid_lyric_id, is_valid_section_id,
)
from .models import SECTION_TYPES, Beat, LyricLine, MasterSong, Section, Timeline
from .schema import (
    MASTER_SONG_SCHEMA, MASTER_SONG_SCHEMA_VERSION, TIMELINE_SCHEMA_VERSION,
    validate_beat_schema, validate_lyric_line_schema, validate_master_song_schema,
    validate_section_schema, validate_timeline_schema,
)
from .timecode import seconds_to_bar_beat, seconds_to_timecode, timecode_to_seconds
from .wav_inspector import WavMetadata, inspect_wav

__all__ = [
    "AudioInspectionError", "Beat", "InvalidTimecodeError", "LyricLine",
    "MASTER_SONG_SCHEMA", "MASTER_SONG_SCHEMA_VERSION", "MasterSong", "SECTION_TYPES",
    "Section", "TIMELINE_SCHEMA_VERSION", "Timeline", "TimelineValidationError",
    "WavMetadata", "assemble_timeline", "build_beats_for_song", "build_master_song",
    "frame_to_seconds", "generate_audio_id", "generate_beats", "generate_lyric_id",
    "generate_section_id", "inspect_wav", "is_valid_audio_id", "is_valid_lyric_id",
    "is_valid_section_id", "seconds_to_bar_beat", "seconds_to_frame", "seconds_to_timecode",
    "timecode_to_seconds", "validate_beat_schema", "validate_lyric_line_schema",
    "validate_master_song_schema", "validate_section_schema", "validate_timeline_schema",
]
