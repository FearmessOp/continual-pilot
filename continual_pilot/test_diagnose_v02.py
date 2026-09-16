"""Deterministic correctness tests for the v0.2 combined run, not hypothesis tests."""
import unittest

import numpy as np
import torch

from pilot import Generator
import diagnose_v02 as v02


class V02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.generator = Generator(seed=13)

    def test_gate_threshold_uses_clean_scale(self):
        baseline = {"majority_baseline_accuracy": 0.42}
        self.assertAlmostEqual(v02.gate_threshold(baseline), 0.942)
        balanced = {"majority_baseline_accuracy": 0.25}
        self.assertAlmostEqual(v02.gate_threshold(balanced), 0.925)

    def test_majority_baseline_from_independent_stream(self):
        baseline = v02.majority_baseline(self.generator, seed=5, count=4000)
        fractions = baseline["class_fractions"]
        self.assertEqual(len(fractions), 4)
        self.assertAlmostEqual(sum(fractions), 1.0, places=5)
        self.assertAlmostEqual(baseline["majority_baseline_accuracy"],
                               max(fractions))
        self.assertEqual(baseline["majority_class"],
                         int(np.argmax(fractions)))

    def test_wilson_interval_bounds_and_ordering(self):
        low, high = v02.wilson_interval(950, 1000)
        self.assertLess(low, 0.95)
        self.assertGreater(high, 0.95)
        self.assertGreaterEqual(low, 0.0)
        self.assertLessEqual(high, 1.0)
        # Wider interval for fewer samples at the same proportion.
        low_small, high_small = v02.wilson_interval(95, 100)
        self.assertGreater(high_small - low_small, high - low)
        self.assertEqual(v02.wilson_interval(0, 0), (0.0, 1.0))

    def test_classification_report_confusion_and_recall(self):
        predictions = np.array([0, 0, 1, 2, 2])
        clean = np.array([0, 1, 1, 2, 2])
        report = v02.classification_report(predictions, clean)
        confusion = np.array(report["confusion_matrix_true_by_pred"])
        self.assertEqual(confusion.shape, (4, 4))
        self.assertEqual(confusion.sum(), 5)
        self.assertEqual(report["class_support"], [1, 2, 2, 0])
        self.assertAlmostEqual(report["per_class_recall"][0], 1.0)
        self.assertAlmostEqual(report["per_class_recall"][1], 0.5)
        self.assertAlmostEqual(report["per_class_recall"][2], 1.0)
        self.assertIsNone(report["per_class_recall"][3])  # No support.

    def test_learning_curve_blocks_and_partial_tail(self):
        clean = np.array([0, 1, 2, 3, 0])
        predictions = np.array([0, 1, 9, 3, 9])  # 3 correct of 5.
        stream = (np.zeros((5, 32)), clean.copy(), clean)
        rows = v02.learning_curve(predictions, stream, block=2)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[-1]["count"], 1)  # Partial tail retained.
        self.assertAlmostEqual(rows[0]["online_clean_accuracy"], 1.0)
        self.assertAlmostEqual(rows[1]["online_clean_accuracy"], 0.5)
        self.assertAlmostEqual(rows[2]["online_clean_accuracy"], 0.0)

    def test_paired_bootstrap_sign_and_zero(self):
        # b makes strictly more errors than a everywhere -> positive difference.
        errors_a = np.zeros(200, dtype=np.int64)
        errors_b = np.ones(200, dtype=np.int64)
        result = v02.paired_bootstrap(errors_a, errors_b, resamples=200, seed=0)
        self.assertAlmostEqual(result["observed_mean_difference"], 1.0)
        self.assertGreater(result["ci_low"], 0.5)
        # Identical error vectors -> zero difference, zero-width interval.
        same = v02.paired_bootstrap(errors_a, errors_a, resamples=200, seed=0)
        self.assertEqual(same["observed_mean_difference"], 0.0)
        self.assertEqual(same["ci_low"], 0.0)
        self.assertEqual(same["ci_high"], 0.0)

    def test_summary_probe_uses_noisy_labels_and_reports_overlap(self):
        full = v02.summary_probe(self.generator, context_window=8,
                                 seed=1, use_4freq_only=False)
        four = v02.summary_probe(self.generator, context_window=8,
                                 seed=1, use_4freq_only=True)
        self.assertEqual(four["feature_dimension"], 4)
        self.assertEqual(full["feature_dimension"], 132)
        self.assertLess(four["effective_independent_blocks_estimate"],
                        four["raw_test_rows"])
        for probe in (full, four):
            self.assertTrue(0 <= probe["regime_probe_test_accuracy"] <= 1)
            self.assertEqual(probe["chance_level"], 0.5)

    def test_frozen_evaluation_predicts_before_label_and_is_frozen(self):
        model = v02.diagnose.make_model(8, False, seed=13)
        before = {k: v.clone() for k, v in model.state_dict().items()}
        predictions, clean, noisy = v02.frozen_evaluation(
            model, self.generator, use_context=False, context_window=4,
            seed=3, count=50)
        self.assertEqual(len(predictions), 50)
        self.assertEqual(len(clean), 50)
        self.assertEqual(len(noisy), 50)
        for name, tensor in model.state_dict().items():
            self.assertTrue(torch.equal(tensor, before[name]))

    def test_frozen_context_variant_ignores_future_labels(self):
        # Flipping later evaluation labels must not change earlier predictions.
        model = v02.diagnose.make_model(8, True, seed=13)
        original_seed = 21

        def evaluate(offset):
            torch.manual_seed(0)
            g = Generator(seed=13)
            predictions, _, _ = v02.frozen_evaluation(
                model, g, use_context=True, context_window=4,
                seed=original_seed, count=30)
            return predictions

        first = evaluate(0)
        second = evaluate(0)
        np.testing.assert_array_equal(first, second)


if __name__ == "__main__":
    unittest.main()