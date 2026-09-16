"""Gate arithmetic tests using constructed labels; no training or sampling."""
import unittest
from unittest.mock import patch

import numpy as np

from .gate_metrics import classification, online_curve, stationary_gate, wilson_interval


class GateMetricsTests(unittest.TestCase):
    @staticmethod
    def labels():
        return np.arange(20000, dtype=np.int64) % 4

    def test_wilson_known_value_and_extremes(self):
        low, high = wilson_interval(50, 100)
        self.assertAlmostEqual(low, 0.40382982859014716)
        self.assertAlmostEqual(high, 0.5961701714098528)
        self.assertAlmostEqual(wilson_interval(0, 100)[0], 0)
        self.assertAlmostEqual(wilson_interval(100, 100)[1], 1)
        self.assertGreater(wilson_interval(0, 100)[1], 0)
        self.assertLess(wilson_interval(100, 100)[0], 1)

    def test_confusion_orientation_and_absent_class(self):
        report = classification(
            np.array([0, 1, 1, 2]), np.array([0, 0, 1, 2]))
        self.assertEqual(report["confusion_matrix_true_by_pred"], [
            [1, 1, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0]])
        self.assertEqual(report["class_support"], [2, 1, 1, 0])
        self.assertEqual(report["per_class_recall"], [0.5, 1.0, 1.0, None])
        self.assertEqual(report["correct"], 3)
        self.assertEqual(report["clean_accuracy"], 0.75)

    def test_measured_threshold_and_clear_pass(self):
        clean = self.labels()
        report = stationary_gate(clean, clean, clean.copy())
        self.assertTrue(report["passed"])
        self.assertEqual(report["threshold_numerator"], 37)
        self.assertEqual(report["threshold_denominator"], 40)
        self.assertEqual(report["threshold"], 0.925)
        self.assertEqual(report["calibration_class_counts"], [5000] * 4)

    def test_threshold_depends_on_calibration_not_test_predictions(self):
        clean = self.labels()
        calibration = np.repeat(np.arange(4), [7500, 5000, 4000, 3500])
        passed = stationary_gate(clean, clean, calibration)
        failed = stationary_gate((clean + 1) % 4, clean, calibration)
        self.assertEqual(passed["threshold"], 0.9375)
        self.assertEqual(failed["threshold"], passed["threshold"])
        self.assertFalse(failed["passed"])
        self.assertEqual(failed["comparison"], "below_threshold")
        self.assertEqual(failed["required_action"], "stop_for_user")

    def test_lower_bound_equality_does_not_pass(self):
        clean = self.labels()
        calibration = np.repeat(np.arange(4), [7500, 5000, 4000, 3500])
        for lower, expected in (
                (np.nextafter(0.9375, 0).item(), False),
                (0.9375, False),
                (np.nextafter(0.9375, 1).item(), True)):
            with self.subTest(lower=lower):
                with patch(
                        "continual_pilot.line2.gate_metrics.wilson_interval",
                        return_value=[lower, 0.99]):
                    report = stationary_gate(clean, clean, calibration)
                self.assertEqual(report["passed"], expected)
                if not expected:
                    self.assertEqual(report["required_action"], "stop_for_user")
                    self.assertEqual(report["comparison"], "interval_overlaps_threshold")

    def test_point_accuracy_above_threshold_is_not_sufficient(self):
        clean = self.labels()
        predictions = clean.copy()
        predictions[:1480] = (predictions[:1480] + 1) % 4
        report = stationary_gate(predictions, clean, clean.copy())
        self.assertGreater(report["clean_accuracy"], report["threshold"])
        self.assertFalse(report["passed"])
        self.assertEqual(report["comparison"], "interval_overlaps_threshold")

    def test_online_blocks_and_oracle_regret(self):
        predictions = np.array([0, 1, 2, 3, 0])
        clean = np.array([0, 0, 2, 2, 0])
        noisy = np.array([0, 1, 2, 2, 1])
        rows = online_curve(predictions, noisy, clean, block=2)
        self.assertEqual([row["count"] for row in rows], [2, 2, 1])
        self.assertEqual([row["stop_index_exclusive"] for row in rows], [2, 4, 5])
        self.assertEqual([row["oracle_regret"] for row in rows], [-1, 1, 0])
        self.assertEqual([row["online_clean_accuracy"] for row in rows], [.5, .5, 1])
        self.assertNotIn("frozen_clean_accuracy", rows[0])

    def test_invalid_counts_shapes_and_labels_fail(self):
        for correct, total in ((-1, 10), (11, 10), (0, 0), (True, 10), (1.0, 10)):
            with self.assertRaises(ValueError):
                wilson_interval(correct, total)
        clean = self.labels()
        with self.assertRaises(ValueError):
            stationary_gate(clean, clean, clean[:-1])
        with self.assertRaises(ValueError):
            stationary_gate(clean[:-1], clean[:-1], clean)
        for invalid in (np.array([4]), np.array([-1]), np.array([1.0]),
                        np.array([True]), np.array([], dtype=np.int64)):
            with self.assertRaises(ValueError):
                classification(invalid, invalid)
        with self.assertRaises(ValueError):
            classification(np.array([0]), np.array([0, 1]))
        with self.assertRaises(ValueError):
            online_curve(clean, clean, clean, block=0)


if __name__ == "__main__":
    unittest.main()