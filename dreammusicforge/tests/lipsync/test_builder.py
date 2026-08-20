from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.core.hashing import hash_file
from dreammusicforge.generation.models import Candidate
from dreammusicforge.lipsync.adapter import NullLipSyncAdapter
from dreammusicforge.lipsync.builder import apply_lip_sync, build_lip_sync_request
from dreammusicforge.lipsync.errors import LipSyncError
from dreammusicforge.music.models import MasterSong
from dreammusicforge.production.models import Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming

from .fixtures import FfmpegRequiredTestCase, make_clip, make_wav_tone


def _wav_duration_seconds(path: Path) -> float:
    import wave
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def _shot(lip_sync_required: bool, start=10.0, end=15.0) -> Shot:
    return Shot(
        id="SHOT-1", sequence_id="SEQ-1",
        timing=ShotTiming(start_seconds=start, end_seconds=end, song_section="chorus_1"),
        purpose=ShotPurpose(semantic_event_id="SEM-1", narrative_function="n", editorial_function="e"),
        requirements=ShotRequirements(
            performer_id="PERFORMER-1", costume_id="COSTUME-1", world_id="WORLD-1",
            lip_sync_required=lip_sync_required, choreography_complexity="low", camera_motion="static", character_count=1,
        ),
        continuity=ShotContinuity(inherited_state="a", permitted_mutations=(), destination_state="b"),
        acceptance={"identity": 95.0},
    )


class BuildLipSyncRequestTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.clip = make_clip(self.dir / "clip.mp4", duration=5.0)
        self.song = make_wav_tone(self.dir / "song.wav", duration=30.0)
        self.master_song = MasterSong(
            id="AUDIO-test", source_file=str(self.song), duration_seconds=30.0, sample_rate=44100,
            channels=2, bpm=120.0, time_signature="4/4", hash=hash_file(self.song),
        )
        self.candidate = Candidate(
            id="CANDIDATE-1", render_task_id="RENDER-1", provider="kling", model_version="v1",
            file=str(self.clip), file_size_bytes=self.clip.stat().st_size, prompt_hash="a" * 64,
            output_hash=hash_file(self.clip), imported_at="2026-08-05T00:00:00+00:00",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_builds_a_request_with_a_real_extracted_audio_window(self):
        shot = _shot(lip_sync_required=True, start=10.0, end=15.0)
        request = build_lip_sync_request(shot, self.candidate, self.master_song, self.dir / "work")

        self.assertTrue(request.id.startswith("LIPSYNC-"))
        self.assertEqual(request.shot_id, shot.id)
        self.assertEqual(request.candidate_id, self.candidate.id)
        self.assertTrue(Path(request.audio_window_file).exists())
        self.assertAlmostEqual(_wav_duration_seconds(Path(request.audio_window_file)), 5.0, delta=0.5)

    def test_shot_not_requiring_lip_sync_raises(self):
        shot = _shot(lip_sync_required=False)
        with self.assertRaises(LipSyncError):
            build_lip_sync_request(shot, self.candidate, self.master_song, self.dir / "work")

    def test_apply_with_null_adapter_reports_not_applied(self):
        shot = _shot(lip_sync_required=True)
        request = build_lip_sync_request(shot, self.candidate, self.master_song, self.dir / "work")
        result = apply_lip_sync(request, NullLipSyncAdapter())

        self.assertEqual(result.request_id, request.id)
        self.assertEqual(result.status, "not_applied")
        self.assertIsNone(result.output_file)
        self.assertTrue(result.reason)


if __name__ == "__main__":
    unittest.main()
