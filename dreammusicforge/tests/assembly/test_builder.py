from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.assembly.builder import assemble_film
from dreammusicforge.assembly.errors import AssemblyError
from dreammusicforge.assembly.models import Transition
from dreammusicforge.core.hashing import hash_file
from dreammusicforge.generation.models import Candidate
from dreammusicforge.music.models import MasterSong
from dreammusicforge.production.models import Shot, ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming
from dreammusicforge.repair.models import RepairPlan, VerificationResult
from dreammusicforge.verification import inspect_media, measure_audio_rms

from .fixtures import FfmpegRequiredTestCase, make_clip, make_wav_tone


def _shot(shot_id, start, end):
    return Shot(
        id=shot_id, sequence_id="SEQ-1", timing=ShotTiming(start_seconds=start, end_seconds=end, song_section="s"),
        purpose=ShotPurpose(semantic_event_id="SEM-1", narrative_function="n", editorial_function="e"),
        requirements=ShotRequirements(
            performer_id="PERFORMER-1", costume_id="COSTUME-1", world_id="WORLD-1",
            lip_sync_required=False, choreography_complexity="low", camera_motion="static", character_count=1,
        ),
        continuity=ShotContinuity(inherited_state="a", permitted_mutations=(), destination_state="b"),
        acceptance={"identity": 95.0},
    )


def _candidate(candidate_id, file_path):
    return Candidate(
        id=candidate_id, render_task_id=f"RENDER-{candidate_id}", provider="kling", model_version="v1",
        file=str(file_path), file_size_bytes=file_path.stat().st_size, prompt_hash="a" * 64,
        output_hash=hash_file(file_path), imported_at="2026-08-05T00:00:00+00:00",
        verification_status="passed", decision="accept",
    )


def _accepted_result(candidate_id):
    return VerificationResult(candidate_id=candidate_id, metrics={"audio": 100.0}, critical_failures=(), overall_score=100.0, decision="accept")


class AssembleFilmTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.clip1 = make_clip(self.dir / "clip1.mp4", color="red", duration=3.0, size="480x854")
        self.clip2 = make_clip(self.dir / "clip2.mp4", color="blue", duration=4.0, size="720x1280", frame_rate=30.0)
        self.song = make_wav_tone(self.dir / "song.wav", duration=10.0)
        self.master_song = MasterSong(
            id="AUDIO-test", source_file=str(self.song), duration_seconds=10.0, sample_rate=44100,
            channels=2, bpm=120.0, time_signature="4/4", hash=hash_file(self.song),
        )
        self.candidate1 = _candidate("CANDIDATE-1", self.clip1)
        self.candidate2 = _candidate("CANDIDATE-2", self.clip2)
        self.shot1 = _shot("SHOT-1", 0.0, 3.0)
        self.shot2 = _shot("SHOT-2", 3.0, 7.0)

    def tearDown(self):
        self._tmp.cleanup()

    def test_accepted_shots_assemble_into_one_video_with_uninterrupted_song(self):
        """Release 0.11's stated acceptance test (spec section 19):
        accepted shots assemble into one video with uninterrupted song."""
        output_path = self.dir / "final.mp4"
        manifest = assemble_film(
            master_song=self.master_song,
            accepted=((self.candidate1, _accepted_result("CANDIDATE-1")), (self.candidate2, _accepted_result("CANDIDATE-2"))),
            shots_by_candidate_id={"CANDIDATE-1": self.shot1, "CANDIDATE-2": self.shot2},
            output_width=512, output_height=910, output_frame_rate=24.0,
            work_dir=self.dir / "work", output_path=output_path, created_at="2026-08-05T00:00:00+00:00",
        )

        self.assertTrue(manifest.id.startswith("EXPORT-"))
        self.assertEqual(manifest.output_hash, hash_file(output_path))
        self.assertEqual([clip.candidate_id for clip in manifest.clips], ["CANDIDATE-1", "CANDIDATE-2"])

        media = inspect_media(output_path)
        self.assertTrue(media.has_audio)
        self.assertAlmostEqual(media.duration_seconds, manifest.total_duration_seconds, places=0)
        audio = measure_audio_rms(output_path)
        self.assertFalse(audio.silent, "assembled audio must be continuous and audible, not silent")

    def test_clips_are_reordered_chronologically_by_shot_start(self):
        output_path = self.dir / "final.mp4"
        manifest = assemble_film(
            master_song=self.master_song,
            # deliberately passed out of order
            accepted=((self.candidate2, _accepted_result("CANDIDATE-2")), (self.candidate1, _accepted_result("CANDIDATE-1"))),
            shots_by_candidate_id={"CANDIDATE-1": self.shot1, "CANDIDATE-2": self.shot2},
            output_width=480, output_height=854, output_frame_rate=24.0,
            work_dir=self.dir / "work", output_path=output_path, created_at="2026-08-05T00:00:00+00:00",
        )
        self.assertEqual([clip.candidate_id for clip in manifest.clips], ["CANDIDATE-1", "CANDIDATE-2"])
        self.assertEqual(manifest.clips[0].start_seconds_in_final, 0.0)
        self.assertGreater(manifest.clips[1].start_seconds_in_final, 0.0)

    def test_rejected_candidate_raises(self):
        rejected_result = VerificationResult(
            candidate_id="CANDIDATE-2", metrics={"continuity": 20.0}, critical_failures=("continuity",),
            overall_score=20.0, decision="reject",
            repair=RepairPlan(shot_id="SHOT-2", action="regenerate"),
        )
        with self.assertRaises(AssemblyError):
            assemble_film(
                master_song=self.master_song,
                accepted=((self.candidate1, _accepted_result("CANDIDATE-1")), (self.candidate2, rejected_result)),
                shots_by_candidate_id={"CANDIDATE-1": self.shot1, "CANDIDATE-2": self.shot2},
                output_width=480, output_height=854, output_frame_rate=24.0,
                work_dir=self.dir / "work", output_path=self.dir / "final.mp4", created_at="2026-08-05T00:00:00+00:00",
            )

    def test_mismatched_verification_result_raises(self):
        wrong_result = _accepted_result("CANDIDATE-999")  # doesn't match candidate1's id
        with self.assertRaises(AssemblyError):
            assemble_film(
                master_song=self.master_song,
                accepted=((self.candidate1, wrong_result),),
                shots_by_candidate_id={"CANDIDATE-1": self.shot1},
                output_width=480, output_height=854, output_frame_rate=24.0,
                work_dir=self.dir / "work", output_path=self.dir / "final.mp4", created_at="2026-08-05T00:00:00+00:00",
            )

    def test_non_executable_transition_type_raises(self):
        dip_to_black = Transition(
            source_shot_id="SHOT-1", destination_shot_id="SHOT-2", transition_type="dip_to_black",
            duration_seconds=1.0, musical_anchor="phrase end", visual_bridge="fade through black", semantic_purpose="soften the cut",
        )
        with self.assertRaises(AssemblyError):
            assemble_film(
                master_song=self.master_song,
                accepted=((self.candidate1, _accepted_result("CANDIDATE-1")), (self.candidate2, _accepted_result("CANDIDATE-2"))),
                shots_by_candidate_id={"CANDIDATE-1": self.shot1, "CANDIDATE-2": self.shot2},
                output_width=480, output_height=854, output_frame_rate=24.0,
                work_dir=self.dir / "work", output_path=self.dir / "final.mp4", created_at="2026-08-05T00:00:00+00:00",
                transitions=(dip_to_black,),
            )

    def test_dissolve_transition_crossfades_and_shortens_total_duration(self):
        """Added after reviewing a real professionally-produced
        reference video in this session: it relies on more than hard
        cuts, so `dissolve` is now executed via ffmpeg's `xfade` filter
        rather than failing closed like the other eight named
        transition types still do."""
        dissolve_duration = 1.0
        dissolve = Transition(
            source_shot_id="SHOT-1", destination_shot_id="SHOT-2", transition_type="dissolve",
            duration_seconds=dissolve_duration, musical_anchor="phrase end", visual_bridge="cross-fade", semantic_purpose="soften the cut",
        )
        output_path = self.dir / "final.mp4"
        manifest = assemble_film(
            master_song=self.master_song,
            accepted=((self.candidate1, _accepted_result("CANDIDATE-1")), (self.candidate2, _accepted_result("CANDIDATE-2"))),
            shots_by_candidate_id={"CANDIDATE-1": self.shot1, "CANDIDATE-2": self.shot2},
            output_width=480, output_height=854, output_frame_rate=24.0,
            work_dir=self.dir / "work", output_path=output_path, created_at="2026-08-05T00:00:00+00:00",
            transitions=(dissolve,),
        )

        self.assertEqual(len(manifest.transitions), 1)
        # Clip 1 is 3s, clip 2 is 4s; a 1s crossfade overlaps them, so
        # the assembled timeline should be shorter than a plain 7s
        # hard-cut concatenation of the same two clips.
        self.assertLess(manifest.total_duration_seconds, 7.0)
        second_clip = next(c for c in manifest.clips if c.candidate_id == "CANDIDATE-2")
        self.assertAlmostEqual(second_clip.start_seconds_in_final, 3.0 - dissolve_duration, delta=0.5)

        media = inspect_media(output_path)
        self.assertTrue(media.has_audio)
        audio = measure_audio_rms(output_path)
        self.assertFalse(audio.silent)

    def test_dissolve_duration_not_shorter_than_either_clip_raises(self):
        too_long_dissolve = Transition(
            source_shot_id="SHOT-1", destination_shot_id="SHOT-2", transition_type="dissolve",
            duration_seconds=10.0,  # longer than either 3s/4s source clip
            musical_anchor="phrase end", visual_bridge="cross-fade", semantic_purpose="soften the cut",
        )
        with self.assertRaises(AssemblyError):
            assemble_film(
                master_song=self.master_song,
                accepted=((self.candidate1, _accepted_result("CANDIDATE-1")), (self.candidate2, _accepted_result("CANDIDATE-2"))),
                shots_by_candidate_id={"CANDIDATE-1": self.shot1, "CANDIDATE-2": self.shot2},
                output_width=480, output_height=854, output_frame_rate=24.0,
                work_dir=self.dir / "work", output_path=self.dir / "final.mp4", created_at="2026-08-05T00:00:00+00:00",
                transitions=(too_long_dissolve,),
            )

    def test_transition_not_matching_an_adjacent_pair_raises(self):
        stray = Transition(
            source_shot_id="SHOT-1", destination_shot_id="SHOT-999",  # SHOT-999 doesn't exist in this assembly
            transition_type="hard_cut", duration_seconds=0.0,
            musical_anchor="phrase end", visual_bridge="none", semantic_purpose="n/a",
        )
        with self.assertRaises(AssemblyError):
            assemble_film(
                master_song=self.master_song,
                accepted=((self.candidate1, _accepted_result("CANDIDATE-1")), (self.candidate2, _accepted_result("CANDIDATE-2"))),
                shots_by_candidate_id={"CANDIDATE-1": self.shot1, "CANDIDATE-2": self.shot2},
                output_width=480, output_height=854, output_frame_rate=24.0,
                work_dir=self.dir / "work", output_path=self.dir / "final.mp4", created_at="2026-08-05T00:00:00+00:00",
                transitions=(stray,),
            )

    def test_hard_cut_transition_is_accepted(self):
        hard_cut = Transition(
            source_shot_id="SHOT-1", destination_shot_id="SHOT-2", transition_type="hard_cut",
            duration_seconds=0.0, musical_anchor="downbeat", visual_bridge="none", semantic_purpose="deliberate scene change",
        )
        manifest = assemble_film(
            master_song=self.master_song,
            accepted=((self.candidate1, _accepted_result("CANDIDATE-1")), (self.candidate2, _accepted_result("CANDIDATE-2"))),
            shots_by_candidate_id={"CANDIDATE-1": self.shot1, "CANDIDATE-2": self.shot2},
            output_width=480, output_height=854, output_frame_rate=24.0,
            work_dir=self.dir / "work", output_path=self.dir / "final.mp4", created_at="2026-08-05T00:00:00+00:00",
            transitions=(hard_cut,),
        )
        self.assertEqual(len(manifest.transitions), 1)

    def test_missing_shot_mapping_raises(self):
        with self.assertRaises(AssemblyError):
            assemble_film(
                master_song=self.master_song,
                accepted=((self.candidate1, _accepted_result("CANDIDATE-1")),),
                shots_by_candidate_id={},  # missing
                output_width=480, output_height=854, output_frame_rate=24.0,
                work_dir=self.dir / "work", output_path=self.dir / "final.mp4", created_at="2026-08-05T00:00:00+00:00",
            )


if __name__ == "__main__":
    unittest.main()
