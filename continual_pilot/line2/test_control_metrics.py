"""Control-decision tests with artificial predictions and explicit mock state."""
import unittest
from unittest.mock import Mock

import numpy as np

from .control_metrics import cpr_activity_control, expert_usage, reference_comparison
from .learner import Learner
from .records import tree_digest


class ControlMetricsTests(unittest.TestCase):
    def test_two_point_limit_inclusive_and_one_error_beyond_fails(self):
        clean = np.arange(20000, dtype=np.int64) % 4
        for errors, expected in ((400, True), (401, False)):
            system = clean.copy()
            system[:errors] = (system[:errors] + 1) % 4
            report = reference_comparison(
                "B", system_predictions=system, clean=clean,
                reference_predictions={"A": clean, "A_expert1": clean})
            self.assertEqual(report["passed"], expected)
            self.assertEqual(
                report["comparisons"]["primary"]["reference_minus_system_correct"],
                errors)

    def test_d_reuses_c_and_secondary_cannot_replace_primary(self):
        clean = np.arange(20000, dtype=np.int64) % 4
        system = (clean + 1) % 4
        report = reference_comparison(
            "D", system_predictions=system, clean=clean,
            reference_predictions={"C": clean, "C_expert1": system})
        self.assertFalse(report["passed"])
        self.assertEqual(report["comparisons"]["primary"]["reference_run"], "C")
        self.assertFalse(report["comparisons"]["secondary"]["used_for_decision"])
        self.assertFalse(report["ideal_frozen_expert_selection_used_as_reference"])

    def test_system_better_than_reference_passes(self):
        clean = np.arange(20000, dtype=np.int64) % 4
        report = reference_comparison(
            "B", system_predictions=clean, clean=clean,
            reference_predictions={"A": (clean + 1) % 4, "A_expert1": clean})
        self.assertTrue(report["passed"])
        self.assertLess(
            report["comparisons"]["primary"]["reference_minus_system_accuracy"], 0)

    def test_invalid_reference_inputs_fail(self):
        clean = np.arange(20000, dtype=np.int64) % 4
        with self.assertRaises(ValueError):
            reference_comparison("A", system_predictions=clean,
                                 reference_predictions={}, clean=clean)
        with self.assertRaises(ValueError):
            reference_comparison(
                "B", system_predictions=clean[:-1], clean=clean,
                reference_predictions={"A": clean, "A_expert1": clean})
        with self.assertRaises(KeyError):
            reference_comparison(
                "D", system_predictions=clean, clean=clean,
                reference_predictions={"A": clean, "A_expert1": clean})

    def test_usage_is_read_only_and_rejects_inconsistent_counts(self):
        learner = Learner("B", seeds={"model0": 7, "model1": 8})
        before = tree_digest(learner.checkpoint())
        report = expert_usage(learner)
        self.assertEqual(report["global_group_opportunities"], 0)
        self.assertEqual(len(report["experts"]), 2)
        self.assertEqual(tree_digest(learner.checkpoint()), before)
        learner.selected_groups[0] = 1
        with self.assertRaises(AssertionError):
            expert_usage(learner)

    @staticmethod
    def activity_fixture():
        report = {
            key: [0.01] * 64 for key in (
                "incoming_path_norm", "outgoing_path_norm",
                "incoming_reference_norm", "outgoing_reference_norm",
                "incoming_relative_path", "outgoing_relative_path",
                "incoming_relative_path_quantiles", "outgoing_relative_path_quantiles")
        }
        report.update({
            "intervention_count": 8,
            "incoming_relative_path_median": 0.001,
            "outgoing_relative_path_median": 0.001,
        })
        return report

    def test_activity_threshold_clock_and_phase_reference(self):
        cpr = Mock(local_updates=2500)
        cpr.activity.return_value = self.activity_fixture()
        incoming, outgoing = object(), object()
        report = cpr_activity_control(
            cpr, phase_start_incoming=incoming, phase_start_outgoing=outgoing)
        self.assertTrue(report["passed"])
        cpr.activity.assert_called_once_with(
            start_update=2436, incoming_reference=incoming,
            outgoing_reference=outgoing)
        self.assertEqual(report["expected_intervention_count"], 8)

    def test_activity_insufficient_motion_wrong_clock_and_nonfinite_fail(self):
        for key, value in (
                ("incoming_relative_path_median", np.nextafter(.001, 0).item()),
                ("intervention_count", 7),
                ("incoming_relative_path", [float("nan")]),
                ("outgoing_relative_path_median", float("inf"))):
            with self.subTest(key=key):
                cpr = Mock(local_updates=2500)
                cpr.activity.return_value = self.activity_fixture()
                cpr.activity.return_value[key] = value
                report = cpr_activity_control(
                    cpr, phase_start_incoming=None, phase_start_outgoing=None)
                self.assertFalse(report["passed"])
        with self.assertRaises(ValueError):
            cpr_activity_control(
                Mock(local_updates=63),
                phase_start_incoming=None, phase_start_outgoing=None)


if __name__ == "__main__":
    unittest.main()