"""Gate mechanics tests; mocked outcomes are not empirical gate evidence."""
import unittest
from unittest.mock import patch

import numpy as np
import torch

import diagnose
import gate_v03 as gate


class ToyGenerator:
    def __init__(self):
        self.calls = []

    def sample(self, count, mixture, rule, rng):
        self.calls.append((count, mixture, rule))
        x = rng.normal(size=(count, 32)).astype(np.float32)
        clean = (x[:, 0] > 0).astype(np.int64)
        return x, clean.copy(), clean, x[:, :8]


def evaluation_record(interval, target_hash="shared"):
    return {
        "frozen_clean_accuracy": sum(interval) / 2,
        "frozen_clean_wilson_95": list(interval),
        "clean_targets_sha256": target_hash,
        "noisy_targets_sha256": target_hash,
    }


class GateV03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_decision_including_exact_boundaries(self):
        self.assertEqual(gate.decision((0.94, 0.96), 0.93), "passed")
        self.assertEqual(gate.decision((0.90, 0.92), 0.93), "failed")
        for interval in ((0.92, 0.94), (0.93, 0.95), (0.91, 0.93)):
            self.assertEqual(gate.decision(interval, 0.93), "indeterminate")

    def test_frozen_evaluation_uses_requested_mixture_and_keeps_weights(self):
        generator = ToyGenerator()
        model = diagnose.make_model(8, False, seed=7)
        before = diagnose.state_digest(model)
        result = gate.evaluate(
            model, generator, mixture=1, seed=120400, count=40)
        self.assertEqual(generator.calls, [(256, 1, 0), (40, 1, 0)])
        self.assertEqual(before, diagnose.state_digest(model))
        self.assertTrue(result["weights_unchanged"])
        self.assertEqual(result["stream_seed"], 120401)
        self.assertEqual(sum(result["class_support"]), 40)
        self.assertEqual(np.sum(result["confusion_matrix_true_by_pred"]), 40)

    def run_small_gate(self, primary_interval, other_hash="shared"):
        generator = ToyGenerator()
        outcomes = [
            evaluation_record(primary_interval),
            evaluation_record((0.98, 0.99), other_hash),
            evaluation_record((0.98, 0.99)),
            evaluation_record((0.94, 0.96)),
        ]
        baseline = {"majority_baseline_accuracy": 0.30}
        with patch.dict(gate.PROTOCOL, {"training_count": 32, "evaluation_count": 40}):
            with patch.object(gate.diagnostics, "majority_baseline",
                              return_value=baseline) as calibrate:
                with patch.object(gate, "evaluate", side_effect=outcomes) as evaluate:
                    report = gate.run_gate(generator)
        calibrate.assert_called_once_with(
            generator, seed=120200, count=20000)
        self.assertEqual(generator.calls, [(32, 0, 0)])
        for entry in report["controls"].values():
            self.assertEqual(entry["optimizer_steps"], 2)
            self.assertEqual(entry["learning_curve"][0]["count"], 32)
        return report, evaluate

    def test_capacity_success_cannot_replace_failed_primary(self):
        report, evaluate = self.run_small_gate((0.89, 0.91))
        self.assertEqual(report["gate_decision"], "failed")
        self.assertEqual(report["controls"]["128"]["gate_comparison"], "passed")
        self.assertEqual(report["controls"]["256"]["gate_comparison"], "passed")
        self.assertEqual(evaluate.call_count, 3)
        self.assertIsNone(report["m2_evaluation"])

    def test_indeterminate_primary_does_not_trigger_m2(self):
        report, evaluate = self.run_small_gate((0.92, 0.94))
        self.assertEqual(report["gate_decision"], "indeterminate")
        self.assertEqual(evaluate.call_count, 3)
        self.assertIsNone(report["m2_evaluation"])

    def test_pass_triggers_m2_with_same_primary_model(self):
        report, evaluate = self.run_small_gate((0.94, 0.96))
        self.assertEqual(report["gate_decision"], "passed")
        self.assertEqual(evaluate.call_count, 4)
        self.assertIsNotNone(report["m2_evaluation"])
        first, last = evaluate.call_args_list[0], evaluate.call_args_list[-1]
        self.assertIs(first.args[0], last.args[0])
        self.assertEqual(last.kwargs, {"mixture": 1, "seed": 120400, "count": 40})
        self.assertEqual(first.kwargs, {"mixture": 0, "seed": 120300, "count": 40})

    def test_unpaired_evaluation_targets_abort_run(self):
        with self.assertRaisesRegex(AssertionError, "share evaluation targets"):
            self.run_small_gate((0.94, 0.96), other_hash="different")


if __name__ == "__main__":
    unittest.main()