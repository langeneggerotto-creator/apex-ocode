from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path

from dreammusicforge.music.builder import assemble_timeline, build_beats_for_song, build_master_song
from dreammusicforge.music.errors import TimelineValidationError
from dreammusicforge.music.ids import generate_audio_id
from dreammusicforge.music.models import LyricLine, Section


def _write_wav(path: Path, seconds: float, sample_rate: int = 44100, channels: int = 2, sample_width: int = 2) -> None:
    frame_count = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sample_width)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00" * (frame_count * channels * sample_width))


class BuildMasterSongTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "song.wav"
        _write_wav(self.path, seconds=4.0)

    def tearDown(self):
        self._tmp.cleanup()

    def test_builds_a_valid_master_song(self):
        song = build_master_song(self.path, bpm=120.0, time_signature="4/4")
        self.assertTrue(song.id.startswith("AUDIO-"))
        self.assertEqual(song.source_file, str(self.path))
        self.assertAlmostEqual(song.duration_seconds, 4.0, places=3)
        self.assertEqual(song.sample_rate, 44100)
        self.assertEqual(song.channels, 2)
        self.assertEqual(song.bpm, 120.0)
        self.assertEqual(song.time_signature, "4/4")
        self.assertTrue(song.hash)

    def test_explicit_song_id_is_used(self):
        chosen_id = generate_audio_id()
        song = build_master_song(self.path, bpm=120.0, time_signature="4/4", song_id=chosen_id)
        self.assertEqual(song.id, chosen_id)

    def test_stems_are_carried_through(self):
        song = build_master_song(self.path, bpm=120.0, time_signature="4/4", stems={"vocals": "vocals.wav"})
        self.assertEqual(song.stems, {"vocals": "vocals.wav"})

    def test_missing_source_file_raises(self):
        from dreammusicforge.music.errors import AudioInspectionError

        with self.assertRaises(AudioInspectionError):
            build_master_song(self.path.parent / "missing.wav", bpm=120.0, time_signature="4/4")


class BuildBeatsForSongTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "song.wav"
        _write_wav(self.path, seconds=2.0)

    def tearDown(self):
        self._tmp.cleanup()

    def test_uses_songs_own_duration_and_bpm(self):
        song = build_master_song(self.path, bpm=120.0, time_signature="4/4")
        beats = build_beats_for_song(song, beats_per_bar=4)
        self.assertEqual(len(beats), 4)
        self.assertTrue(all(beat.time < song.duration_seconds for beat in beats))


class AssembleTimelineTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "song.wav"
        _write_wav(self.path, seconds=4.0)
        self.song = build_master_song(self.path, bpm=120.0, time_signature="4/4")

    def tearDown(self):
        self._tmp.cleanup()

    def test_one_song_becomes_a_canonical_timeline(self):
        """Release 0.2's stated acceptance test (spec section 19): one
        song can become a canonical timeline."""
        beats = build_beats_for_song(self.song, beats_per_bar=4)
        sections = (
            Section(id="SECTION-1", type="verse", start_seconds=0.0, end_seconds=2.0),
            Section(id="SECTION-2", type="chorus", start_seconds=2.0, end_seconds=4.0),
        )
        lyric_lines = (
            LyricLine(id="LYRIC-1", start_seconds=0.0, end_seconds=1.5, text="a placeholder lyric line"),
        )

        timeline = assemble_timeline(self.song, sections=sections, beats=beats, lyric_lines=lyric_lines)

        self.assertEqual(timeline.master_song_id, self.song.id)
        self.assertEqual(timeline.sections, sections)
        self.assertEqual(timeline.beats, beats)
        self.assertEqual(timeline.lyric_lines, lyric_lines)

    def test_empty_timeline_is_valid(self):
        timeline = assemble_timeline(self.song)
        self.assertEqual(timeline.sections, ())
        self.assertEqual(timeline.beats, ())
        self.assertEqual(timeline.lyric_lines, ())

    def test_overlapping_sections_raise(self):
        sections = (
            Section(id="SECTION-1", type="verse", start_seconds=0.0, end_seconds=3.0),
            Section(id="SECTION-2", type="chorus", start_seconds=2.0, end_seconds=4.0),
        )
        with self.assertRaises(TimelineValidationError):
            assemble_timeline(self.song, sections=sections)

    def test_error_carries_every_problem_found(self):
        sections = (
            Section(id="SECTION-1", type="verse", start_seconds=0.0, end_seconds=3.0),
            Section(id="SECTION-2", type="chorus", start_seconds=2.0, end_seconds=4.0),
        )
        lyric_lines = (
            LyricLine(id="LYRIC-1", start_seconds=0.0, end_seconds=2.0, text="line one"),
            LyricLine(id="LYRIC-2", start_seconds=1.0, end_seconds=3.0, text="line two"),
        )
        try:
            assemble_timeline(self.song, sections=sections, lyric_lines=lyric_lines)
            self.fail("expected TimelineValidationError")
        except TimelineValidationError as exc:
            self.assertGreaterEqual(len(exc.errors), 2)


if __name__ == "__main__":
    unittest.main()
