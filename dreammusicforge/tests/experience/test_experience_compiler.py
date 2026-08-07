import unittest

from dreammusicforge.experience import compile_experience_graph, validate_experience_graph


class ExperienceCompilerTests(unittest.TestCase):
    def _valid_payload(self):
        return {
            "version": "0.1",
            "duration_seconds": 10.0,
            "transformation": {"from": "uncertain", "to": "hopeful"},
            "checkpoints": [
                {
                    "t_start": 0.0,
                    "t_end": 5.0,
                    "primary_experience": "curiosity",
                    "intensity": 0.4,
                    "attention_goal": "stay oriented",
                    "memory_goal": "remember the threshold",
                    "intended_inference": "something is about to change",
                    "evidence_status": "INFERRED",
                },
                {
                    "t_start": 5.0,
                    "t_end": 10.0,
                    "primary_experience": "hope",
                    "intensity": 0.8,
                    "attention_goal": "focus on performer",
                    "memory_goal": "remember the release",
                    "intended_inference": "change is possible",
                    "evidence_status": "INFERRED",
                },
            ],
        }

    def test_valid_graph_compiles(self):
        graph = compile_experience_graph(self._valid_payload())
        self.assertEqual(graph.duration_seconds, 10.0)
        self.assertEqual(len(graph.checkpoints), 2)

    def test_gap_fails(self):
        payload = self._valid_payload()
        payload["checkpoints"][1]["t_start"] = 6.0
        with self.assertRaises(ValueError):
            compile_experience_graph(payload)

    def test_overlap_fails(self):
        payload = self._valid_payload()
        payload["checkpoints"][1]["t_start"] = 4.0
        with self.assertRaises(ValueError):
            compile_experience_graph(payload)

    def test_invalid_intensity_fails(self):
        payload = self._valid_payload()
        payload["checkpoints"][0]["intensity"] = 1.5
        with self.assertRaises(ValueError):
            compile_experience_graph(payload)

    def test_missing_transformation_fails(self):
        payload = self._valid_payload()
        payload["transformation"] = {"from": "", "to": ""}
        with self.assertRaises(ValueError):
            compile_experience_graph(payload)

    def test_contradictory_checkpoint_fails(self):
        payload = self._valid_payload()
        payload["checkpoints"][0]["prohibited_inference"] = ["something is about to change"]
        with self.assertRaises(ValueError):
            compile_experience_graph(payload)

    def test_validator_returns_machine_readable_issue_codes(self):
        graph = compile_experience_graph(self._valid_payload())
        self.assertEqual(validate_experience_graph(graph), ())


if __name__ == "__main__":
    unittest.main()
