"""Recorded-training integration tests; temporary artifacts and artificial inputs."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import torch

from .data import learner_seeds
from .learner import BASE_METHODS, Learner
from .records import Records, tree_digest
from .training import train_recorded


class TrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.previous_threads)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        rng = np.random.default_rng(1234)
        self.x = rng.normal(size=(128, 32)).astype(np.float32)
        self.y = np.arange(128, dtype=np.int64) % 4
        self.seeds = learner_seeds("mechanics-test", 5)

    def test_recording_matches_direct_training_for_all_base_methods(self):
        for method in BASE_METHODS:
            with self.subTest(method=method):
                learner = Learner(method, seeds=self.seeds)
                direct = learner.fork()
                records = Records(self.root / method.replace("+", "_"))
                result = train_recorded(
                    records, "run", learner, x=self.x[:32], noisy=self.y[:32],
                    verification_inputs=self.x[:4])
                expected = []
                for row, label in zip(self.x[:32], self.y[:32]):
                    expected.append(direct.predict(row))
                    direct.observe(label)
                np.testing.assert_array_equal(result["predictions"], expected)
                self.assertEqual(tree_digest(learner.checkpoint()),
                                 tree_digest(direct.checkpoint()))
                report = result["report"]
                self.assertEqual(report["new_examples"], 32)
                self.assertEqual(report["global_group_opportunities"], 2)
                self.assertEqual(sum(report["expert_optimizer_updates"]),
                                 0 if method == "knn" else 2)
                self.assertEqual(report["router_optimizer_updates"],
                                 2 if method in ("B", "D") else 0)
                with np.load(records.root / "run/online.npz") as stored:
                    np.testing.assert_array_equal(stored["predictions"], expected)
                    np.testing.assert_array_equal(stored["index"], np.arange(32))
                records.finish()

    def test_replay_ragged_indices_and_batch_accounting(self):
        learner = Learner("replay", seeds=self.seeds)
        records = Records(self.root / "replay")
        result = train_recorded(
            records, "run", learner, x=self.x[:32], noisy=self.y[:32],
            verification_inputs=self.x[:4])
        expected_replay = sum(min(i, 8) for i in range(32))
        self.assertEqual(result["report"]["sampled_replay_examples"], expected_replay)
        self.assertEqual(sum(result["report"]["training_examples_by_expert"]),
                         32 + expected_replay)
        self.assertEqual(result["report"]["maximum_training_batch"], 144)
        with np.load(records.root / "run/online.npz") as stored:
            indices = stored["sampled_replay_indices"]
            offsets = stored["sampled_replay_offsets"]
            self.assertEqual(len(offsets), 33)
            self.assertEqual(offsets[-1], len(indices))
            for i in range(32):
                selected = indices[offsets[i]:offsets[i + 1]]
                self.assertEqual(len(selected), min(i, 8))
                self.assertTrue(np.all((selected >= 0) & (selected < i)))

    def test_cpr_records_full_event_and_original_phase_weights(self):
        learner = Learner("C", seeds=self.seeds)
        original = learner.experts[0].model[0].weight.detach().clone()
        records = Records(self.root / "cpr")
        result = train_recorded(
            records, "run", learner, x=self.x, noisy=self.y,
            verification_inputs=self.x[:4])
        self.assertEqual(result["report"]["cpr_per_example_gradient_evaluations"], [128])
        self.assertTrue(torch.equal(result["phase_start_weights"]["expert0_incoming"],
                                    original))
        final = torch.load(records.root / "run/final.pt", weights_only=True)
        events = final["experts"][0]["cpr"]["events"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["local_update"], 8)
        self.assertIn("incoming_before", events[0])
        self.assertIn("incoming_after", events[0])
        with np.load(records.root / "run/groups.npz") as stored:
            self.assertTrue(stored["utility_valid"].all())
            self.assertTrue(np.isfinite(stored["raw_utility"]).all())
            self.assertFalse(stored["router_valid"].any())

    def test_invalid_or_partial_data_is_rejected_before_writes(self):
        learner = Learner("A", seeds=self.seeds)
        before = tree_digest(learner.checkpoint())
        for x, y in ((self.x[:17], self.y[:17]),
                     (self.x[:16], self.y[:15]),
                     (self.x[:16].astype(np.float64), self.y[:16])):
            records = Mock()
            with self.assertRaises(ValueError):
                train_recorded(records, "run", learner, x=x, noisy=y,
                               verification_inputs=self.x[:4])
            self.assertEqual(records.mock_calls, [])
            self.assertEqual(tree_digest(learner.checkpoint()), before)


if __name__ == "__main__":
    unittest.main()