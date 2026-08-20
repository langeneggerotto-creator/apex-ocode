"""Release 1.0 -- Benchmark 007: the end-to-end capstone.

Not verified against the original spec's own text for this release --
only the name "Benchmark 007" survived this session's context
compaction, with no further detail about what the "007" refers to.
Interpreted here as this repository's own acceptance benchmark: one
real, synthetic-but-genuine run through every release built this
session (0.1 through 0.15), on ffmpeg-generated fixtures rather than
placeholder objects, asserting the whole chain actually produces a
playable, finished film plus its lip-sync request, composite demo, and
operator report -- not that each stage merely "didn't raise."

This mirrors the same real-data pipeline shape this session already
proved out three times by hand against genuine Kling AI footage
(referred to elsewhere in this session as the "hope," "burgundy," and
"rooftop" runs) -- Benchmark 007 is that same shape turned into a
permanent, synthetic, CI-runnable regression test instead of a
one-off scratch script.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dreammusicforge.assembly import Transition, assemble_film
from dreammusicforge.compositing import CompositeLayer, build_composite
from dreammusicforge.core import Project, generate_project_id, validate_project_schema
from dreammusicforge.finishing import finish_film
from dreammusicforge.generation import import_candidate
from dreammusicforge.genome import CameraLanguage, ColorLanguage, assemble_film_genome, build_costume, build_performer, build_world
from dreammusicforge.lipsync import NullLipSyncAdapter, apply_lip_sync, build_lip_sync_request
from dreammusicforge.music.builder import build_master_song
from dreammusicforge.operator_studio import build_operator_report, create_operator_server, render_report_html
from dreammusicforge.production import (
    assemble_production_graph, build_semantic_event, build_sequence, build_shot,
)
from dreammusicforge.production.models import ShotContinuity, ShotPurpose, ShotRequirements, ShotTiming
from dreammusicforge.repair import evaluate_candidate, score_technical_report
from dreammusicforge.verification import generate_technical_report, inspect_media, measure_audio_rms

from .fixtures import FfmpegRequiredTestCase, make_clip_with_tone, make_wav_tone


class Benchmark007EndToEndTests(FfmpegRequiredTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_full_pipeline_0_1_through_0_15_produces_a_finished_film(self):
        d = self.dir

        # ---- 0.1 Project Kernel ----
        project = Project(
            id=generate_project_id(), title="Benchmark 007", version="1.0.0", status="compiling",
            aspect_ratio="9:16", resolution="480x854", frame_rate=24,
            target_duration_seconds=6.0, providers=("kling",),
            created_at="2026-08-20T00:00:00+00:00", updated_at="2026-08-20T00:00:00+00:00",
        )
        self.assertEqual(validate_project_schema(project.to_dict()), [])

        # ---- 0.2 Master Song ----
        song_wav = make_wav_tone(d / "song.wav", duration=10.0)
        master_song = build_master_song(song_wav, bpm=120.0, time_signature="4/4")

        # ---- 0.3 Film Genome ----
        performer = build_performer(
            display_name="Benchmark Performer", reference_assets=(str(song_wav),),
            immutable={"apparent_age": "20s", "face_geometry": "oval", "body_proportions": "average", "skin_tone": "fair", "eye_color": "brown", "identifying_features": "none"},
            mutable_by_contract={"expression": "varies", "pose": "varies", "gaze": "varies", "costume": "locked", "hair_configuration": "locked"},
        )
        costume = build_costume(topology={"neckline": "crew"}, material="cotton", references={"front": str(song_wav)})
        world = build_world(type="studio", references={"wide": str(song_wav)}, geometry="plain studio", palette="neutral", lighting="flat", atmosphere="none")
        film_genome = assemble_film_genome(
            transformation_from="setup", transformation_to="payoff",
            performers=(performer,), costumes=(costume,), worlds=(world,),
            camera_language=CameraLanguage(lens_vocabulary=("35mm",), movement_vocabulary=("static",)),
            color_language=ColorLanguage(opening="neutral", development="neutral", climax="neutral"),
            motifs=("benchmark",), invariants=("lead_performer_identity", "costume_topology_within_scene", "world_geometry_within_scene"),
        )

        # ---- 0.4 Production Graph (editorial-chapters: per-sequence camera/color override) ----
        sequence = build_sequence(
            song_section="verse_1", start_seconds=0.0, end_seconds=6.0,
            camera_language=CameraLanguage(lens_vocabulary=("85mm",), movement_vocabulary=("slow_push",)),
            color_language=ColorLanguage(opening="warm", development="warm", climax="warm"),
        )
        event = build_semantic_event(start_seconds=0.0, end_seconds=6.0, meaning="a benchmark completes", transformation_from="setup", transformation_to="payoff")
        shot1 = build_shot(
            sequence_id=sequence.id, timing=ShotTiming(start_seconds=0.0, end_seconds=3.0, song_section="verse_1"),
            purpose=ShotPurpose(semantic_event_id=event.id, narrative_function="establish", editorial_function="wide"),
            requirements=ShotRequirements(performer_id=performer.id, costume_id=costume.id, world_id=world.id, lip_sync_required=False, choreography_complexity="low", camera_motion="static", character_count=1),
            continuity=ShotContinuity(inherited_state="start", permitted_mutations=(), destination_state="mid"),
            acceptance={"identity": 90.0},
        )
        shot2 = build_shot(
            sequence_id=sequence.id, timing=ShotTiming(start_seconds=3.0, end_seconds=6.0, song_section="verse_1"),
            purpose=ShotPurpose(semantic_event_id=event.id, narrative_function="reveal", editorial_function="close"),
            requirements=ShotRequirements(performer_id=performer.id, costume_id=costume.id, world_id=world.id, lip_sync_required=True, choreography_complexity="low", camera_motion="static", character_count=1),
            continuity=ShotContinuity(inherited_state="mid", permitted_mutations=(), destination_state="end"),
            acceptance={"identity": 90.0, "lip_sync": 80.0},
        )
        production_graph = assemble_production_graph(film_genome=film_genome, sequences=(sequence,), semantic_events=(event,), shots=(shot1, shot2))
        self.assertEqual([s.id for s in production_graph.shots], [shot1.id, shot2.id])

        # ---- 0.8 Candidate Intake ----
        clip1 = make_clip_with_tone(d / "clip1.mp4", color="red", duration=3.0)
        clip2 = make_clip_with_tone(d / "clip2.mp4", color="red", duration=3.0)
        candidate1 = import_candidate(render_task_id="RENDER-1", provider="kling", model_version="v1", file_path=clip1, prompt="benchmark shot 1", imported_at="2026-08-20T00:00:00+00:00")
        candidate2 = import_candidate(render_task_id="RENDER-2", provider="kling", model_version="v1", file_path=clip2, prompt="benchmark shot 2", imported_at="2026-08-20T00:00:00+00:00")

        # ---- 0.9 Technical Verification ----
        report1 = generate_technical_report(candidate_id=candidate1.id, file_path=clip1, expected_duration_seconds=3.0, expected_frame_rate=24.0)
        report2 = generate_technical_report(candidate_id=candidate2.id, file_path=clip2, expected_duration_seconds=3.0, expected_frame_rate=24.0)
        self.assertTrue(report1.passed)
        self.assertTrue(report2.passed)

        # ---- 0.10 Acceptance and Repair Engine ----
        result1 = evaluate_candidate(candidate_id=candidate1.id, shot_id=shot1.id, metrics=score_technical_report(report1))
        result2 = evaluate_candidate(candidate_id=candidate2.id, shot_id=shot2.id, metrics=score_technical_report(report2))
        self.assertEqual(result1.decision, "accept")
        self.assertEqual(result2.decision, "accept")

        # ---- 0.11 Assembly Engine (with a dissolve, exercising the editorial-chapters addition) ----
        output_path = d / "assembled.mp4"
        dissolve = Transition(
            source_shot_id=shot1.id, destination_shot_id=shot2.id, transition_type="dissolve",
            duration_seconds=0.5, musical_anchor="phrase boundary", visual_bridge="cross-fade",
            semantic_purpose="soften the cut into the payoff",
        )
        manifest = assemble_film(
            master_song=master_song, accepted=((candidate1, result1), (candidate2, result2)),
            shots_by_candidate_id={candidate1.id: shot1, candidate2.id: shot2},
            output_width=480, output_height=854, output_frame_rate=24.0,
            work_dir=d / "assembly-work", output_path=output_path, created_at="2026-08-20T00:00:00+00:00",
            transitions=(dissolve,),
        )
        self.assertTrue(Path(manifest.output_file).exists())
        final_media = inspect_media(Path(manifest.output_file))
        self.assertTrue(final_media.has_audio)
        self.assertFalse(measure_audio_rms(Path(manifest.output_file)).silent)

        # ---- 0.12 Lip-Sync Adapter (shot2 requires it) ----
        lip_sync_request = build_lip_sync_request(shot2, candidate2, master_song, d / "lipsync-work")
        lip_sync_result = apply_lip_sync(lip_sync_request, NullLipSyncAdapter())
        self.assertTrue(Path(lip_sync_request.audio_window_file).exists())
        self.assertEqual(lip_sync_result.status, "not_applied")

        # ---- 0.13 Masking and Compositing (standalone demo, not wired into assembly's clip list) ----
        background = make_clip_with_tone(d / "bg.mp4", color="blue", duration=1.0, size="64x64")
        foreground = make_clip_with_tone(d / "fg.mp4", color="green", duration=1.0, size="64x64")
        composite_result = build_composite(
            shot_id=shot1.id,
            background=CompositeLayer(layer_type="background", source_file=str(background)),
            foreground=CompositeLayer(layer_type="foreground", source_file=str(foreground), mask_type="chromakey", chroma_color="green"),
            work_dir=d / "composite-work",
        )
        self.assertTrue(Path(composite_result.output_file).exists())

        # ---- 0.14 Color and Audio Finishing ----
        finishing_result = finish_film(manifest, d / "finishing-work")
        self.assertTrue(Path(finishing_result.output_file).exists())
        finished_media = inspect_media(Path(finishing_result.output_file))
        self.assertTrue(finished_media.has_audio)
        self.assertFalse(measure_audio_rms(Path(finishing_result.output_file)).silent)

        # ---- 0.15 Operator Studio ----
        report = build_operator_report(
            verification_results=(result1, result2), export_manifests=(manifest,),
            finishing_results=(finishing_result,), generated_at="2026-08-20T00:00:00+00:00",
        )
        html = render_report_html(report)
        self.assertIn(candidate1.id, html)
        self.assertIn(candidate2.id, html)
        self.assertIn(manifest.id, html)
        self.assertIn(finishing_result.id, html)

        server = create_operator_server(report, host="127.0.0.1", port=0)
        try:
            import threading
            import urllib.request

            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=5) as response:
                self.assertEqual(response.status, 200)
                served_html = response.read().decode("utf-8")
            self.assertIn(manifest.id, served_html)
        finally:
            server.shutdown()
            server.server_close()

        # ---- Final capstone assertion: a genuinely finished, playable film exists ----
        self.assertGreater(Path(finishing_result.output_file).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
