"""Deterministic correctness tests for the diagnostics, not hypothesis tests."""
import copy
import unittest

import numpy as np
import torch
from torch import nn

from pilot import Generator
import diagnose


class DiagnoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.generator = Generator(seed=13)

    def test_same_shape_initialization_is_independent_of_probe_rng(self):
        first = diagnose.make_model(64, True, seed=7)
        features = np.array([[-1.0], [1.0]], dtype=np.float32)
        diagnose.logistic_probe(features, np.array([0, 1]), epochs=2, seed=507)
        torch.rand(100)
        second = diagnose.make_model(64, True, seed=7)
        for name, value in first.state_dict().items():
            self.assertTrue(torch.equal(value, second.state_dict()[name]))
        self.assertEqual(diagnose.state_digest(first), diagnose.state_digest(second))

    def test_seeded_initialization_matches_original_pilot(self):
        import pilot
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(7)
            original = pilot.make_model(64)
        actual = diagnose.make_model(64, True, seed=7)
        self.assertEqual(diagnose.state_digest(original), diagnose.state_digest(actual))

    def test_prediction_comparison_rejects_equal_accuracy_different_sequences(self):
        left = np.array([0, 1, 2, 3], dtype=np.int64)
        self.assertTrue(diagnose.prediction_comparison(left, left.copy())["bitwise_equal"])
        with self.assertRaises(AssertionError):
            diagnose.prediction_comparison(left, np.array([1, 0, 2, 3], dtype=np.int64))

    def test_training_prefix_and_original_pilot_predictions_match(self):
        import pilot
        from types import SimpleNamespace
        reference = diagnose.single_regime(self.generator, 40, 113)
        tail = diagnose.single_regime(self.generator, 20, 114)
        extended = tuple(np.concatenate((a, b)) for a, b in zip(reference, tail))
        initial = diagnose.make_model(8, True, seed=13)
        options = dict(lr=.001, use_context=True, context_window=4,
                       minibatch=1, seed=13)
        _, _, short_predictions, _, _ = diagnose.train_online(initial, reference, **options)
        _, _, long_predictions, _, _ = diagnose.train_online(initial, extended, **options)
        args = SimpleNamespace(lr=.001, context_window=4, capacity=512,
                               replay_batch=8, seed=13, hidden=8)
        original = pilot.run(initial, reference, args)["predictions"]
        self.assertTrue(diagnose.prediction_comparison(
            original, short_predictions)["bitwise_equal"])
        self.assertTrue(diagnose.prediction_comparison(
            long_predictions[:40], short_predictions)["bitwise_equal"])

    def test_model_width_tracks_context(self):
        with_context = diagnose.make_model(8, True)
        without_context = diagnose.make_model(8, False)
        self.assertEqual(with_context[0].in_features, 164)
        self.assertEqual(without_context[0].in_features, 32)

    def test_encode_without_context_is_raw_input(self):
        x = np.arange(32, dtype=np.float32)
        encoded = diagnose.encode(None, x, False)
        np.testing.assert_array_equal(encoded, x)
        self.assertEqual(encoded.dtype, np.float32)

    def test_long_stream_shares_reference_prefix(self):
        generator = self.generator
        seed = 100
        reference = diagnose.single_regime(generator, 20, seed)
        tail = diagnose.single_regime(generator, 30, seed + 1)
        long_stream = tuple(np.concatenate((reference[i], tail[i]))
                            for i in range(3))
        for i in range(3):
            np.testing.assert_array_equal(long_stream[i][:20], reference[i])
        self.assertEqual(len(long_stream[1]), 50)

    def test_minibatch_step_count_and_partial_group(self):
        stream = diagnose.single_regime(self.generator, 10, 5)
        base = diagnose.make_model(8, True)
        for minibatch, expected in ((1, 10), (4, 3), (16, 1)):
            _, _, predictions, steps, _ = diagnose.train_online(
                base, stream, lr=1e-3, use_context=True,
                context_window=4, minibatch=minibatch, seed=1)
            self.assertEqual(steps, expected)
            self.assertEqual(len(predictions), 10)

    def test_prediction_precedes_label_even_within_group(self):
        stream = diagnose.single_regime(self.generator, 8, 9)
        changed = tuple(array.copy() for array in stream)
        changed[1][3:] = (changed[1][3:] + 1) % 4  # Alter labels from index 3.
        base = diagnose.make_model(8, True)
        _, _, left, _, _ = diagnose.train_online(
            base, stream, lr=1e-2, use_context=True,
            context_window=4, minibatch=16, seed=2)
        _, _, right, _, _ = diagnose.train_online(
            base, changed, lr=1e-2, use_context=True,
            context_window=4, minibatch=16, seed=2)
        # Predictions up to index 3 cannot depend on labels from index 3 on.
        np.testing.assert_array_equal(left[:4], right[:4])

    def test_frozen_evaluation_does_not_change_weights(self):
        base = diagnose.make_model(8, True)
        before = copy.deepcopy(base.state_dict())
        diagnose.frozen_accuracy(base, self.generator, use_context=True,
                                 context_window=4, seed=3)
        for name, tensor in base.state_dict().items():
            self.assertTrue(torch.equal(tensor, before[name]))

    def test_summarise_regret_matches_oracle(self):
        stream = (np.zeros((4, 32)), np.array([0, 1, 2, 3]),
                  np.array([0, 1, 2, 0]))
        result = diagnose.summarise(stream[2].copy(), stream, tail=2)
        self.assertEqual(result["total_regret"], 0)
        self.assertAlmostEqual(result["online_accuracy"], 0.75)
        self.assertAlmostEqual(result["oracle_accuracy"], 0.75)

    def test_logistic_probe_separates_easy_classes(self):
        rng = np.random.default_rng(0)
        left = rng.normal(-3, 0.2, size=(80, 2))
        right = rng.normal(3, 0.2, size=(80, 2))
        features = np.concatenate((left, right)).astype(np.float32)
        labels = np.concatenate((np.zeros(80), np.ones(80)))
        probe = diagnose.logistic_probe(features, labels, epochs=200, seed=0)
        with torch.no_grad():
            prediction = probe(torch.from_numpy(features)).argmax(dim=1).numpy()
        self.assertGreater(np.mean(prediction == labels), 0.95)

    def test_probe_and_balance_shapes(self):
        probe = diagnose.context_summary_probe(
            self.generator, context_window=8, seed=1)
        self.assertEqual(probe["chance_level"], 0.5)
        self.assertGreater(probe["test_examples"], 0)
        self.assertTrue(0 <= probe["regime_probe_test_accuracy"] <= 1)
        balance = diagnose.balance_diagnostic(
            self.generator, seed=2, count=2000)
        for mixture in ("M1", "M2"):
            fractions = balance[mixture]["debiased_R1_class_fractions"]
            self.assertEqual(len(fractions), 4)
            self.assertAlmostEqual(sum(fractions), 1.0, places=5)


if __name__ == "__main__":
    unittest.main()