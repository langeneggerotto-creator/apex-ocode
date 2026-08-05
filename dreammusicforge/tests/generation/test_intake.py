from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from dreammusicforge.core.hashing import hash_text
from dreammusicforge.generation.errors import CandidateIntakeError
from dreammusicforge.generation.intake import import_candidate


class ImportCandidateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.candidate_file = self.dir / "CANDIDATE-021-B-003.mp4"
        self.candidate_file.write_bytes(b"fake rendered video bytes for testing")

    def tearDown(self):
        self._tmp.cleanup()

    def test_every_imported_candidate_is_traceable(self):
        """Release 0.8's stated acceptance test (spec section 19): every
        imported candidate is traceable -- its hash independently proves
        which file was imported, and its fields trace back to the
        render task and prompt that produced it."""
        prompt = "Create 6.5 seconds of cinematic video.\n"
        candidate = import_candidate(
            render_task_id="RENDER-021-B", provider="kling", model_version="kling-v1.6",
            file_path=self.candidate_file, prompt=prompt, imported_at="2026-08-05T12:00:00+00:00",
        )

        self.assertTrue(candidate.id.startswith("CANDIDATE-"))
        self.assertEqual(candidate.render_task_id, "RENDER-021-B")
        expected_hash = hashlib.sha256(self.candidate_file.read_bytes()).hexdigest()
        self.assertEqual(candidate.output_hash, expected_hash)
        self.assertEqual(candidate.prompt_hash, hash_text(prompt))
        self.assertEqual(candidate.file_size_bytes, self.candidate_file.stat().st_size)
        self.assertEqual(candidate.verification_status, "pending")
        self.assertEqual(candidate.decision, "pending")

    def test_reference_paths_are_hashed(self):
        ref_path = self.dir / "face_front.png"
        ref_path.write_bytes(b"fake reference image bytes")
        candidate = import_candidate(
            render_task_id="RENDER-021-B", provider="kling", model_version="kling-v1.6",
            file_path=self.candidate_file, prompt="a prompt", imported_at="2026-08-05T12:00:00+00:00",
            reference_paths=(ref_path,),
        )
        self.assertEqual(candidate.reference_hashes, (hashlib.sha256(ref_path.read_bytes()).hexdigest(),))

    def test_explicit_candidate_id_is_used(self):
        from dreammusicforge.generation.ids import generate_candidate_id
        chosen_id = generate_candidate_id()
        candidate = import_candidate(
            render_task_id="RENDER-021-B", provider="kling", model_version="kling-v1.6",
            file_path=self.candidate_file, prompt="a prompt", imported_at="2026-08-05T12:00:00+00:00",
            candidate_id=chosen_id,
        )
        self.assertEqual(candidate.id, chosen_id)

    def test_missing_candidate_file_raises(self):
        with self.assertRaises(CandidateIntakeError):
            import_candidate(
                render_task_id="RENDER-021-B", provider="kling", model_version="kling-v1.6",
                file_path=self.dir / "does-not-exist.mp4", prompt="a prompt", imported_at="2026-08-05T12:00:00+00:00",
            )

    def test_missing_reference_file_raises(self):
        with self.assertRaises(CandidateIntakeError):
            import_candidate(
                render_task_id="RENDER-021-B", provider="kling", model_version="kling-v1.6",
                file_path=self.candidate_file, prompt="a prompt", imported_at="2026-08-05T12:00:00+00:00",
                reference_paths=(self.dir / "missing-reference.png",),
            )

    def test_different_files_produce_different_hashes(self):
        other_file = self.dir / "other-candidate.mp4"
        other_file.write_bytes(b"different content entirely")
        candidate_a = import_candidate(
            render_task_id="RENDER-021-B", provider="kling", model_version="kling-v1.6",
            file_path=self.candidate_file, prompt="a prompt", imported_at="2026-08-05T12:00:00+00:00",
        )
        candidate_b = import_candidate(
            render_task_id="RENDER-021-B", provider="kling", model_version="kling-v1.6",
            file_path=other_file, prompt="a prompt", imported_at="2026-08-05T12:00:00+00:00",
        )
        self.assertNotEqual(candidate_a.output_hash, candidate_b.output_hash)


if __name__ == "__main__":
    unittest.main()
