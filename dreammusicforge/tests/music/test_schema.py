from __future__ import annotations

import copy
import unittest

from dreammusicforge.music.schema import (
    validate_beat_schema, validate_lyric_line_schema, validate_master_song_schema,
    validate_section_schema, validate_timeline_schema,
)

VALID_MASTER_SONG = {
    "id": "AUDIO-deadbeef",
    "source_file": "songs/begin_again.wav",
    "duration_seconds": 180.5,
    "sample_rate": 44100,
    "channels": 2,
    "bpm": 120.0,
    "time_signature": "4/4",
    "hash": "abc123",
}

VALID_SECTION = {"id": "SECTION-1", "type": "verse", "start_seconds": 0.0, "end_seconds": 10.0}
VALID_BEAT = {"index": 0, "time": 0.0, "bar": 1, "beat_in_bar": 1}
VALID_LYRIC_LINE = {"id": "LYRIC-1", "start_seconds": 0.0, "end_seconds": 2.0, "text": "a line"}

VALID_TIMELINE = {
    "master_song_id": "AUDIO-deadbeef",
    "sections": [VALID_SECTION, {"id": "SECTION-2", "type": "chorus", "start_seconds": 10.0, "end_seconds": 20.0}],
    "beats": [VALID_BEAT, {"index": 1, "time": 0.5, "bar": 1, "beat_in_bar": 2}],
    "lyric_lines": [VALID_LYRIC_LINE, {"id": "LYRIC-2", "start_seconds": 2.0, "end_seconds": 4.0, "text": "another line"}],
}


class MasterSongSchemaTests(unittest.TestCase):
    def test_valid_master_song_has_no_errors(self):
        self.assertEqual(validate_master_song_schema(VALID_MASTER_SONG), [])

    def test_stems_may_be_omitted(self):
        self.assertEqual(validate_master_song_schema(VALID_MASTER_SONG), [])

    def test_stems_may_be_present(self):
        data = dict(VALID_MASTER_SONG, stems={"vocals": "songs/vocals.wav"})
        self.assertEqual(validate_master_song_schema(data), [])

    def test_non_dict_is_rejected(self):
        self.assertTrue(validate_master_song_schema(["not", "a", "dict"]))

    def test_missing_required_field_is_reported(self):
        data = copy.deepcopy(VALID_MASTER_SONG)
        del data["bpm"]
        errors = validate_master_song_schema(data)
        self.assertTrue(any("bpm" in e for e in errors))

    def test_zero_bpm_is_rejected(self):
        data = dict(VALID_MASTER_SONG, bpm=0)
        errors = validate_master_song_schema(data)
        self.assertTrue(any("bpm" in e for e in errors))

    def test_negative_duration_is_rejected(self):
        data = dict(VALID_MASTER_SONG, duration_seconds=-1)
        errors = validate_master_song_schema(data)
        self.assertTrue(any("duration_seconds" in e for e in errors))

    def test_non_string_stems_values_are_rejected(self):
        data = dict(VALID_MASTER_SONG, stems={"vocals": 123})
        errors = validate_master_song_schema(data)
        self.assertTrue(any("stems" in e for e in errors))

    def test_stems_must_be_object(self):
        data = dict(VALID_MASTER_SONG, stems=["vocals"])
        errors = validate_master_song_schema(data)
        self.assertTrue(any("stems" in e for e in errors))


class SectionSchemaTests(unittest.TestCase):
    def test_valid_section_has_no_errors(self):
        self.assertEqual(validate_section_schema(VALID_SECTION), [])

    def test_invalid_type_is_rejected(self):
        data = dict(VALID_SECTION, type="climax")
        errors = validate_section_schema(data)
        self.assertTrue(any("type" in e for e in errors))

    def test_start_after_end_is_rejected(self):
        data = dict(VALID_SECTION, start_seconds=20.0, end_seconds=10.0)
        errors = validate_section_schema(data)
        self.assertTrue(any("start_seconds" in e for e in errors))

    def test_negative_start_is_rejected(self):
        data = dict(VALID_SECTION, start_seconds=-1.0)
        errors = validate_section_schema(data)
        self.assertTrue(any("start_seconds" in e for e in errors))

    def test_empty_label_is_rejected(self):
        data = dict(VALID_SECTION, label="")
        errors = validate_section_schema(data)
        self.assertTrue(any("label" in e for e in errors))

    def test_null_label_is_accepted(self):
        data = dict(VALID_SECTION, label=None)
        self.assertEqual(validate_section_schema(data), [])


class BeatSchemaTests(unittest.TestCase):
    def test_valid_beat_has_no_errors(self):
        self.assertEqual(validate_beat_schema(VALID_BEAT), [])

    def test_zero_bar_is_rejected(self):
        data = dict(VALID_BEAT, bar=0)
        errors = validate_beat_schema(data)
        self.assertTrue(any("bar" in e for e in errors))

    def test_negative_index_is_rejected(self):
        data = dict(VALID_BEAT, index=-1)
        errors = validate_beat_schema(data)
        self.assertTrue(any("index" in e for e in errors))

    def test_bool_is_rejected_for_index(self):
        data = dict(VALID_BEAT, index=True)
        errors = validate_beat_schema(data)
        self.assertTrue(any("index" in e for e in errors))


class LyricLineSchemaTests(unittest.TestCase):
    def test_valid_lyric_line_has_no_errors(self):
        self.assertEqual(validate_lyric_line_schema(VALID_LYRIC_LINE), [])

    def test_empty_text_is_rejected(self):
        data = dict(VALID_LYRIC_LINE, text="")
        errors = validate_lyric_line_schema(data)
        self.assertTrue(any(e for e in errors))

    def test_start_after_end_is_rejected(self):
        data = dict(VALID_LYRIC_LINE, start_seconds=5.0, end_seconds=1.0)
        errors = validate_lyric_line_schema(data)
        self.assertTrue(any("start_seconds" in e for e in errors))


class TimelineSchemaTests(unittest.TestCase):
    def test_valid_timeline_has_no_errors(self):
        self.assertEqual(validate_timeline_schema(VALID_TIMELINE), [])

    def test_missing_master_song_id_is_reported(self):
        data = copy.deepcopy(VALID_TIMELINE)
        del data["master_song_id"]
        errors = validate_timeline_schema(data)
        self.assertTrue(any("master_song_id" in e for e in errors))

    def test_overlapping_sections_are_rejected(self):
        data = copy.deepcopy(VALID_TIMELINE)
        data["sections"] = [
            {"id": "SECTION-1", "type": "verse", "start_seconds": 0.0, "end_seconds": 15.0},
            {"id": "SECTION-2", "type": "chorus", "start_seconds": 10.0, "end_seconds": 20.0},
        ]
        errors = validate_timeline_schema(data)
        self.assertTrue(any("overlap" in e for e in errors))

    def test_overlapping_lyric_lines_are_rejected(self):
        data = copy.deepcopy(VALID_TIMELINE)
        data["lyric_lines"] = [
            {"id": "LYRIC-1", "start_seconds": 0.0, "end_seconds": 3.0, "text": "a line"},
            {"id": "LYRIC-2", "start_seconds": 2.0, "end_seconds": 5.0, "text": "another line"},
        ]
        errors = validate_timeline_schema(data)
        self.assertTrue(any("overlap" in e for e in errors))

    def test_adjacent_non_overlapping_sections_are_accepted(self):
        data = copy.deepcopy(VALID_TIMELINE)
        data["sections"] = [
            {"id": "SECTION-1", "type": "verse", "start_seconds": 0.0, "end_seconds": 10.0},
            {"id": "SECTION-2", "type": "chorus", "start_seconds": 10.0, "end_seconds": 20.0},
        ]
        self.assertEqual(validate_timeline_schema(data), [])

    def test_invalid_nested_section_is_reported_with_index(self):
        data = copy.deepcopy(VALID_TIMELINE)
        data["sections"] = [{"id": "SECTION-1", "type": "not-a-real-type", "start_seconds": 0.0, "end_seconds": 10.0}]
        errors = validate_timeline_schema(data)
        self.assertTrue(any(e.startswith("sections[0]") for e in errors))

    def test_sections_not_a_list_is_rejected(self):
        data = dict(VALID_TIMELINE, sections="not-a-list")
        errors = validate_timeline_schema(data)
        self.assertTrue(any("sections" in e for e in errors))

    def test_empty_timeline_is_valid(self):
        self.assertEqual(validate_timeline_schema({"master_song_id": "AUDIO-deadbeef"}), [])

    def test_duplicate_beat_indices_are_rejected(self):
        data = copy.deepcopy(VALID_TIMELINE)
        data["beats"] = [
            {"index": 0, "time": 0.0, "bar": 1, "beat_in_bar": 1},
            {"index": 0, "time": 0.5, "bar": 1, "beat_in_bar": 2},
        ]
        errors = validate_timeline_schema(data)
        self.assertTrue(any("duplicated" in e for e in errors))

    def test_unique_beat_indices_are_accepted(self):
        data = copy.deepcopy(VALID_TIMELINE)
        self.assertEqual(validate_timeline_schema(data), [])


if __name__ == "__main__":
    unittest.main()
