"""Audit bookkeeping tests; synthetic metrics are not empirical acceptance data."""
import unittest
from unittest.mock import Mock, call, patch

import robustness_v03 as robustness


def metrics(category):
    fractions = [0.25] * 4
    if category in ("balance_only", "both"):
        fractions = [0.10, 0.30, 0.30, 0.30]
    disagreement = 0.80 if category in ("disagreement_only", "both") else 0.55
    return {
        "class_fractions": {
            name: list(fractions)
            for name in ("M1_R1", "M1_R2", "M2_R1", "M2_R2")
        },
        "disagreement": {"M1": disagreement, "M2": disagreement},
        "min_class_fraction": min(fractions),
        "max_class_fraction": max(fractions),
    }


class RobustnessV03Tests(unittest.TestCase):
    def run_audit(self, categories):
        generators = [Mock(offset_seed=91000 + i) for i in range(20)]
        with patch.object(
                robustness.gv3, "GeneratorV03", side_effect=generators) as factory:
            with patch.object(
                    robustness.gv3, "acceptance_metrics",
                    side_effect=[metrics(c) for c in categories]) as measure:
                report = robustness.audit()
        self.assertEqual(factory.call_args_list, [
            call(seed=1000 + i, alpha=0.5, noise=0.05, calibration_count=20000)
            for i in range(20)
        ])
        self.assertEqual(measure.call_args_list, [
            call(generators[i], seed=50000 + i, count=20000)
            for i in range(20)
        ])
        return report

    def test_first_acceptance_does_not_stop_audit_and_reasons_partition(self):
        categories = ["accepted", "balance_only", "disagreement_only", "both"] * 5
        report = self.run_audit(categories)
        self.assertEqual(report["counts"], {
            "accepted": 5, "balance_only": 5, "disagreement_only": 5, "both": 5})
        self.assertEqual(report["acceptance_rate"], 0.25)
        self.assertEqual(report["selected_generator_seed_unchanged"], 1000)
        self.assertFalse(report["protocol"]["early_stopping"])
        expected_reasons = [
            [], ["balance"], ["disagreement"], ["balance", "disagreement"]]
        self.assertEqual(len(report["records"]), 20)
        for index, record in enumerate(report["records"]):
            self.assertEqual(record["generator_seed"], 1000 + index)
            self.assertEqual(record["offset_seed"], 91000 + index)
            self.assertEqual(record["metric_seed"], 50000 + index)
            self.assertEqual(record["reasons"], expected_reasons[index % 4])
            self.assertEqual(record["accepted"], index % 4 == 0)
            self.assertEqual(record["metrics"], metrics(categories[index]))

    def test_all_accepted_still_evaluates_twenty_candidates(self):
        report = self.run_audit(["accepted"] * 20)
        self.assertEqual(report["counts"]["accepted"], 20)
        self.assertEqual(sum(report["counts"].values()), 20)
        self.assertEqual(report["acceptance_rate"], 1.0)

    def test_all_rejected_does_not_replace_selected_generator(self):
        report = self.run_audit(["both"] * 20)
        self.assertEqual(report["counts"]["both"], 20)
        self.assertEqual(report["acceptance_rate"], 0.0)
        self.assertEqual(report["selected_generator_seed_unchanged"], 1000)


if __name__ == "__main__":
    unittest.main()