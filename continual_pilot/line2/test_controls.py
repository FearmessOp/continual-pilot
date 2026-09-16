"""Stationary orchestration tests; no experimental training or candidate draws."""
from contextlib import ExitStack
import unittest
from unittest.mock import Mock, patch

import numpy as np
import torch

from .controls import RUN_METHODS, control_learners, frozen_control, run_stationary_condition
from .data import learner_seeds
from .records import tree_digest


class ControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.previous_threads)

    def test_six_unique_learners_have_paired_initialization_and_cpr(self):
        seeds = learner_seeds("mechanics-test", 9)
        learners = control_learners(seeds)
        self.assertEqual(tuple(learners), tuple(name for name, _ in RUN_METHODS))
        self.assertEqual(len({id(value) for value in learners.values()}), 6)
        for index, reference in ((0, "C"), (1, "C_expert1")):
            self.assertEqual(
                tree_digest(learners[reference].experts[0].cpr.state_dict()),
                tree_digest(learners["D"].experts[index].cpr.state_dict()))
            self.assertEqual(
                tree_digest(learners[reference].experts[0].model.state_dict()),
                tree_digest(learners["B"].experts[index].model.state_dict()))

    def test_frozen_control_preserves_state_and_archives_both_experts(self):
        learner = control_learners(learner_seeds("mechanics-test", 9))["D"]
        evaluation = {
            "x": np.zeros((8, 32), dtype=np.float32),
            "index": np.arange(8),
            "r1": np.arange(8) % 4,
            "r2": (np.arange(8) + 1) % 4,
        }
        before = tree_digest(learner.checkpoint())
        records = Mock()
        predictions, reports = frozen_control(records, "run", learner, evaluation)
        self.assertEqual(before, tree_digest(learner.checkpoint()))
        self.assertEqual(predictions.shape, (8,))
        self.assertEqual(len(reports), 2)
        arrays = records.arrays.call_args.args[1]
        self.assertEqual(set(arrays), {
            "index", "system_predictions", "expert0_predictions", "expert1_predictions"})
        for report in reports:
            self.assertEqual(report["R1"]["count"], 8)
            self.assertEqual(report["R2"]["count"], 8)

    def orchestration(self, *, c_passed):
        training = {
            "x": np.zeros((40000, 32), dtype=np.float32),
            "noisy": np.arange(40000) % 4,
            "clean": np.arange(40000) % 4,
        }
        evaluation = {
            "x": np.zeros((20000, 32), dtype=np.float32),
            "clean": np.arange(20000) % 4,
        }
        calibration = {"clean": evaluation["clean"].copy()}
        records = Mock()
        train_calls = []
        prediction_by_name = {}

        def train(_records, directory, learner, *, x, noisy, verification_inputs):
            self.assertIs(x, training["x"])
            self.assertIs(noisy, training["noisy"])
            name = directory.rsplit("/", 1)[-1]
            train_calls.append(name)
            return {
                "report": {"mock_training": True},
                "predictions": np.zeros(40000, dtype=np.int64),
                "phase_start_weights": {
                    "expert0_incoming": learner.experts[0].model[0].weight.detach().clone(),
                    "expert0_outgoing": learner.experts[0].model[2].weight.detach().clone(),
                },
            }

        def frozen(_records, directory, learner, data):
            self.assertIs(data, evaluation)
            name = directory.rsplit("/", 1)[-1]
            prediction = evaluation["clean"].copy()
            prediction_by_name[name] = prediction
            return prediction, []

        comparisons = []

        def compare(method, *, system_predictions, reference_predictions, clean):
            comparisons.append(method)
            self.assertIs(reference_predictions["C"], prediction_by_name["C"])
            self.assertIs(system_predictions, prediction_by_name[method])
            return {"passed": True}

        gate_results = [
            {"passed": True}, {"passed": c_passed},
            *[{"passed": True} for _ in range(4)],
        ]
        with ExitStack() as stack:
            prefix = "continual_pilot.line2.controls."
            stack.enter_context(patch(prefix + "train_recorded", side_effect=train))
            stack.enter_context(patch(prefix + "frozen_control", side_effect=frozen))
            stack.enter_context(patch(prefix + "stationary_gate", side_effect=gate_results))
            stack.enter_context(patch(prefix + "online_curve", return_value=[]))
            stack.enter_context(patch(prefix + "expert_usage", return_value={"mock": True}))
            stack.enter_context(patch(prefix + "cpr_activity_control",
                                      return_value={"passed": True}))
            stack.enter_context(patch(prefix + "reference_comparison", side_effect=compare))
            summary = run_stationary_condition(
                records, "condition", seeds=learner_seeds("mechanics-test", 9),
                training=training, calibration=calibration, evaluation=evaluation)
        self.assertEqual(train_calls, [name for name, _ in RUN_METHODS])
        self.assertEqual(comparisons, ["B", "D"])
        self.assertEqual(summary["unique_training_runs"], 6)
        self.assertEqual(summary["ideal_D_isolated_expert_record_aliases"],
                         {"0": "C", "1": "C_expert1"})
        return summary

    def test_success_uses_c_once_without_duplicate_ideal_training(self):
        summary = self.orchestration(c_passed=True)
        self.assertTrue(summary["passed"])
        self.assertEqual(summary["next_action"], "await_other_controls")

    def test_required_failure_stops_and_is_not_replaced_by_secondary(self):
        summary = self.orchestration(c_passed=False)
        self.assertFalse(summary["passed"])
        self.assertFalse(summary["required_checks"]["C_learnability"])
        self.assertFalse(summary["required_checks"]["ideal_D_expert0_learnability_reuses_C"])
        self.assertEqual(summary["next_action"], "stop_for_user")


if __name__ == "__main__":
    unittest.main()