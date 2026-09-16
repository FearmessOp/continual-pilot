"""Isolated mechanics tests for the asymmetric pilot; no historical file writes."""
import copy
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

import diagnose
from asymmetric_pilot import engine as e
from asymmetric_pilot.run import Records, run_pilot


def small_config():
    config = copy.deepcopy(e.CONFIG)
    config.update(hidden=8, capacity=16, phase1_count=32, phase2_count=32,
                  phase3_candidates=[16, 32], phase4_count=32,
                  evaluation_count=40, window_updates=1, stream_seeds=[230001])
    return config


def data(count=64):
    rng = np.random.default_rng(42)
    x = rng.normal(size=(count, 32)).astype(np.float32)
    y = rng.integers(0, 4, size=count, dtype=np.int64)
    return x, y


class AsymmetricPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def learner(self, replay=True):
        config = small_config()
        return e.Learner(diagnose.make_model(8, False, seed=7),
                         replay=replay, reservoir_seed=234001, config=config)

    def test_fork_preserves_optimizer_buffer_rng_and_prefix(self):
        parent = self.learner()
        x, y = data()
        parent.train_phase(x[:32], y[:32])
        before = e.tree_digest(parent.checkpoint())
        short, long = parent.fork(), parent.fork()
        source_ids = {id(p) for p in parent.model.parameters()}
        child_ids = {id(p) for p in short.model.parameters()}
        optimizer_ids = {id(p) for group in short.optimizer.param_groups
                         for p in group["params"]}
        self.assertTrue(source_ids.isdisjoint(child_ids))
        self.assertEqual(child_ids, optimizer_ids)
        result_short = short.train_phase(x[32:48], y[32:48])
        result_long = long.train_phase(x[32:], y[32:])
        np.testing.assert_array_equal(result_short["predictions"],
                                      result_long["predictions"][:16])
        long_at_same_point = parent.fork()
        long_at_same_point.train_phase(x[32:48], y[32:48])
        self.assertEqual(e.tree_digest(short.checkpoint()),
                         e.tree_digest(long_at_same_point.checkpoint()))
        self.assertEqual(before, e.tree_digest(parent.checkpoint()))
        self.assertNotEqual(before, e.tree_digest(short.checkpoint()))

    def test_checkpoint_roundtrip_preserves_future_training(self):
        learner = self.learner()
        x, y = data()
        learner.train_phase(x[:32], y[:32])
        with tempfile.TemporaryDirectory() as tmp:
            records = Records(Path(tmp) / "run")
            records.checkpoint("state.pt", learner)
            state = torch.load(records.root / "state.pt",
                               map_location="cpu", weights_only=True)
            restored = e.Learner.from_checkpoint(state)
            first = learner.train_phase(x[32:], y[32:])
            second = restored.train_phase(x[32:], y[32:])
            np.testing.assert_array_equal(first["predictions"], second["predictions"])
            self.assertEqual(e.tree_digest(learner.checkpoint()),
                             e.tree_digest(restored.checkpoint()))
            records.arrays("predictions.npz", {"prediction": first["predictions"]})
            records.finish()
            self.assertTrue((records.root / "manifest.json").is_file())
            with self.assertRaises(FileExistsError):
                records.arrays("predictions.npz", {"prediction": first["predictions"]})

    def test_current_and_future_labels_do_not_change_current_prediction(self):
        x, y = data()
        altered = y.copy()
        altered[15:] = (altered[15:] + 1) % 4
        for replay in (False, True):
            with self.subTest(replay=replay):
                initial = self.learner(replay)
                first = initial.fork().train_phase(x, y)
                second = initial.fork().train_phase(x, altered)
                np.testing.assert_array_equal(first["predictions"][:16],
                                              second["predictions"][:16])

    def test_update_counts_partial_group_and_replay_cost(self):
        x, y = data(33)
        for replay in (False, True):
            with self.subTest(replay=replay):
                learner = self.learner(replay)
                result = learner.train_phase(x, y)
                np.testing.assert_array_equal(result["update_positions"], [16, 32, 33])
                self.assertEqual(learner.steps, 3)
                self.assertEqual(learner.examples_seen, 33)
                expected_replay = sum(min(i, 8) for i in range(33)) if replay else 0
                self.assertEqual(result["replay_examples"], expected_replay)
                self.assertEqual(result["maximum_batch"], 144 if replay else 16)

    def test_frozen_evaluation_preserves_complete_state(self):
        learner = self.learner()
        x, y = data()
        learner.train_phase(x, y)
        before = e.tree_digest(learner.checkpoint())
        evaluation = {"x": x, "r1": y, "r2": (y + 1) % 4}
        report, predictions = e.frozen_report(learner, evaluation)
        self.assertEqual(before, e.tree_digest(learner.checkpoint()))
        self.assertEqual(report["r1_accuracy"], float(np.mean(predictions == y)))

    def test_metrics_normalize_and_keep_signed_window_difference(self):
        result = {
            "predictions": np.array([1, 0, 0, 0]),
            "update_positions": np.array([2, 4]),
            "replay_examples": 8, "maximum_batch": 6,
        }
        targets = {"noisy": np.array([0, 1, 0, 0]), "clean": np.zeros(4, dtype=int)}
        metrics = e.phase_metrics(result, targets)
        self.assertEqual(metrics["oracle_regret"], 1)
        self.assertEqual(metrics["oracle_regret_per_example"], 0.25)
        window = e.window_metrics(
            result["predictions"], np.ones(4), targets["clean"],
            result["update_positions"], 4)
        self.assertEqual(window["extra_errors"], -3)
        self.assertEqual(window["updates"], 2)
        self.assertEqual(window["extra_errors_per_example"], -0.75)

    def test_selection_uses_all_A_seeds_and_never_replay(self):
        config = copy.deepcopy(e.CONFIG)
        rows = [
            {"seed": seed, "method": "A", "phase3_count": length,
             "frozen": {"2": {"r1_accuracy": 0.85}}, "damage": 0.30}
            for seed in config["stream_seeds"] for length in [2000, 4000]
        ]
        self.assertEqual(e.select_candidate(rows, config)["selected_phase3_count"], 2000)
        rows[0]["damage"] = 0.41
        self.assertEqual(e.select_candidate(rows, config)["selected_phase3_count"], 4000)
        rows[1]["frozen"]["2"]["r1_accuracy"] = 0.79
        self.assertIsNone(e.select_candidate(rows, config)["selected_phase3_count"])
        replay_rows = [{**r, "method": "replay", "damage": 0.30} for r in rows]
        self.assertIsNone(e.select_candidate(rows + replay_rows, config)[
            "selected_phase3_count"])
        with self.assertRaises(ValueError):
            e.select_candidate(rows[:-1], config)

    def test_small_end_to_end_pilot_writes_all_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = Records(Path(tmp) / "run")
            report = run_pilot(records, small_config())
            self.assertEqual(len(report["rows"]), 4)
            for row in report["rows"]:
                self.assertEqual(row["window"]["count"], 16)
                self.assertEqual(row["window"]["updates"], 1)
                self.assertEqual(row["phase3_updates"], row["phase3_count"] // 16)
                self.assertEqual(row["total_optimizer_steps"],
                                 6 + row["phase3_count"] // 16)
            records.json("summary.json", report)
            records.finish()
            with np.load(records.root / "data/seed230001_phase3.npz",
                         allow_pickle=False) as loaded:
                self.assertEqual(set(loaded.files), {"x", "z", "noisy", "clean", "index"})
                self.assertEqual(len(loaded["x"]), 32)


if __name__ == "__main__":
    unittest.main()