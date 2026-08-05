from __future__ import annotations

import unittest

from dreammusicforge.music.models import Beat, LyricLine, MasterSong, Section, Timeline

MASTER_SONG_DATA = {
    "id": "AUDIO-deadbeef",
    "source_file": "songs/begin_again.wav",
    "duration_seconds": 180.5,
    "sample_rate": 44100,
    "channels": 2,
    "bpm": 120.0,
    "time_signature": "4/4",
    "hash": "abc123",
    "stems": {"vocals": "songs/begin_again_vocals.wav"},
}


class MasterSongRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        song = MasterSong.from_dict(MASTER_SONG_DATA)
        self.assertEqual(song.to_dict(), MASTER_SONG_DATA)

    def test_missing_stems_defaults_to_empty_dict(self):
        data = {k: v for k, v in MASTER_SONG_DATA.items() if k != "stems"}
        song = MasterSong.from_dict(data)
        self.assertEqual(song.stems, {})

    def test_master_song_is_frozen(self):
        song = MasterSong.from_dict(MASTER_SONG_DATA)
        with self.assertRaises(Exception):
            song.bpm = 999  # type: ignore[misc]


class SectionRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        data = {"id": "SECTION-deadbeef", "type": "chorus", "start_seconds": 10.0, "end_seconds": 30.0, "label": None}
        section = Section.from_dict(data)
        self.assertEqual(section.to_dict(), data)

    def test_label_defaults_to_none(self):
        data = {"id": "SECTION-deadbeef", "type": "verse", "start_seconds": 0.0, "end_seconds": 10.0}
        section = Section.from_dict(data)
        self.assertIsNone(section.label)


class LyricLineRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        data = {"id": "LYRIC-deadbeef", "start_seconds": 1.0, "end_seconds": 3.5, "text": "a line of text"}
        line = LyricLine.from_dict(data)
        self.assertEqual(line.to_dict(), data)


class BeatRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        data = {"index": 3, "time": 1.5, "bar": 1, "beat_in_bar": 4}
        beat = Beat.from_dict(data)
        self.assertEqual(beat.to_dict(), data)


class TimelineRoundTripTests(unittest.TestCase):
    def test_from_dict_then_to_dict_round_trips(self):
        data = {
            "master_song_id": "AUDIO-deadbeef",
            "sections": [{"id": "SECTION-1", "type": "verse", "start_seconds": 0.0, "end_seconds": 10.0, "label": None}],
            "beats": [{"index": 0, "time": 0.0, "bar": 1, "beat_in_bar": 1}],
            "lyric_lines": [{"id": "LYRIC-1", "start_seconds": 0.0, "end_seconds": 2.0, "text": "a line"}],
        }
        timeline = Timeline.from_dict(data)
        self.assertEqual(timeline.to_dict(), data)

    def test_missing_collections_default_to_empty_tuples(self):
        timeline = Timeline.from_dict({"master_song_id": "AUDIO-deadbeef"})
        self.assertEqual(timeline.sections, ())
        self.assertEqual(timeline.beats, ())
        self.assertEqual(timeline.lyric_lines, ())

    def test_timeline_is_frozen(self):
        timeline = Timeline(master_song_id="AUDIO-deadbeef")
        with self.assertRaises(Exception):
            timeline.master_song_id = "AUDIO-other"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
