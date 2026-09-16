"""Representation mechanics on artificial arrays, not experimental streams."""
import unittest

import numpy as np
import torch

from .records import tree_digest
from .representation import block_summaries, fit_probe, probe_report


class RepresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.previous_threads)

    @staticmethod
    def summary_fixture():
        targets = np.repeat(np.arange(2, dtype=np.int64), 512)
        features = np.zeros((1024, 132), dtype=np.float32)
        features[:, 0] = 2 * targets - 1
        return features, targets

    def test_blocks_use_shared_inputs_and_separate_noisy_labels(self):
        x = np.repeat(np.arange(512, dtype=np.float32), 64)[:, None]
        x = np.repeat(x, 32, axis=1)
        labels = np.zeros((32768, 2), dtype=np.int64)
        labels[:, 1] = 1
        result = block_summaries(x, labels)
        summary = result["summaries"]
        np.testing.assert_array_equal(summary[:512, 0], np.ones(512))
        np.testing.assert_array_equal(summary[512:, 1], np.ones(512))
        np.testing.assert_array_equal(summary[:512, 4], np.arange(512))
        np.testing.assert_array_equal(summary[512:, 36], np.arange(512))
        np.testing.assert_array_equal(result["start_indices"][:512],
                                      np.arange(512) * 64)
        np.testing.assert_array_equal(result["stop_indices_exclusive"][:512],
                                      (np.arange(512) + 1) * 64)
        changed_x = x.copy()
        changed_x[:64] = -100
        changed = block_summaries(changed_x, labels)["summaries"]
        unaffected = np.ones(1024, dtype=bool)
        unaffected[[0, 512]] = False
        np.testing.assert_array_equal(summary[unaffected], changed[unaffected])

    def test_fixed_budget_and_test_targets_do_not_affect_training(self):
        features, targets = self.summary_fixture()
        before = torch.random.get_rng_state().clone()
        original = features.copy()
        first = fit_probe(features, targets, features.copy(), targets.copy())
        second = fit_probe(features, targets, features.copy(), 1 - targets)
        self.assertEqual(tree_digest(first["state"]), tree_digest(second["state"]))
        np.testing.assert_array_equal(first["predictions"], second["predictions"])
        np.testing.assert_array_equal(features, original)
        self.assertTrue(torch.equal(before, torch.random.get_rng_state()))
        self.assertEqual(first["state"]["updates"], 300)
        self.assertEqual(len(first["training_losses"]), 300)
        for state in first["state"]["optimizer"]["state"].values():
            self.assertEqual(int(state["step"]), 300)
        self.assertFalse(first["report"]["weights_transferred_to_learner"])

    def test_probe_state_recreates_predictions(self):
        features, targets = self.summary_fixture()
        result = fit_probe(features, targets, features, targets)
        with torch.random.fork_rng(devices=[]):
            restored = torch.nn.Linear(132, 2)
        restored.load_state_dict(result["state"]["model"])
        with torch.no_grad():
            predictions = restored(torch.from_numpy(features)).argmax(dim=1).numpy()
        np.testing.assert_array_equal(predictions, result["predictions"])

    def test_balanced_and_raw_accuracy_use_all_test_blocks(self):
        _, targets = self.summary_fixture()
        for errors, expected in ((102, True), (103, False)):
            predictions = targets.copy()
            predictions[:errors] = 1 - predictions[:errors]
            report = probe_report(predictions, targets)
            self.assertEqual(report["passed"], expected)
            self.assertEqual(report["test_blocks_per_rule"], [512, 512])
            self.assertEqual(report["accuracy_per_rule"], [(512 - errors) / 512, 1])
            self.assertEqual(report["raw_accuracy"], (1024 - errors) / 1024)
            self.assertEqual(report["balanced_accuracy"], report["raw_accuracy"])

    def test_invalid_block_shapes_and_labels_fail(self):
        x = np.zeros((32768, 32), dtype=np.float32)
        labels = np.zeros((32768, 2), dtype=np.int64)
        for bad_x, bad_y in ((x[:-1], labels), (x, labels[:-1]),
                             (x, labels.astype(float)), (x, labels + 4)):
            with self.assertRaises(ValueError):
                block_summaries(bad_x, bad_y)
        with self.assertRaises(ValueError):
            probe_report(np.zeros(1024, dtype=np.int64),
                         np.zeros(1024, dtype=np.int64))


if __name__ == "__main__":
    unittest.main()