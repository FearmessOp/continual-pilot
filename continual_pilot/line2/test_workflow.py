"""Workflow stop-rule tests; all scientific sampling/training is mocked."""
from contextlib import ExitStack
import unittest
from unittest.mock import Mock, patch

from .workflow import run_allowed_stages


class WorkflowTests(unittest.TestCase):
    def exercise(self, *, acceptance=True, condition_results=None,
                 representation_results=None, data_error=None):
        records = Mock()
        accepted = [
            {"pair": i, "teacher_seed": 10000 + i, "filtered": object()}
            for i in range(3)
        ] if acceptance else []
        generated = []

        def data(filtered, *, section, pair, role, condition, count):
            if data_error is not None:
                raise data_error
            generated.append((pair, condition, role, count))
            return {
                "arrays": {"fixture": (pair, condition, role)},
                "provenance": {
                    "seed": pair * 100 + condition * 10
                    + {"training": 1, "gate-calibration": 2, "evaluation": 3}[role]
                },
            }

        prefix = "continual_pilot.line2.workflow."
        with ExitStack() as stack:
            pool = stack.enter_context(patch(
                prefix + "run_control_pool",
                return_value=({"accepted": acceptance}, accepted)))
            stack.enter_context(patch(prefix + "stationary_data", side_effect=data))
            save = stack.enter_context(patch(prefix + "save_dataset"))
            conditions = stack.enter_context(patch(
                prefix + "run_stationary_condition",
                side_effect=condition_results or [{"passed": True}] * 6))
            representation = stack.enter_context(patch(
                prefix + "run_representation_control",
                side_effect=representation_results or [{"passed": True}] * 3))
            result = run_allowed_stages(records)
        pool.assert_called_once_with(records)
        self.assertFalse(result["duration_power_main_started"])
        self.assertEqual(result["next_action"], "stop_for_user")
        records.json.assert_any_call("summary.json", result)
        return result, conditions, representation, save, generated

    def test_acceptance_failure_prevents_all_data_and_training(self):
        result, conditions, representation, save, generated = self.exercise(
            acceptance=False)
        self.assertFalse(result["passed"])
        self.assertEqual(result["stop_reason"], "insufficient_accepted_generators")
        self.assertEqual(result["controls"], [])
        self.assertEqual(generated, [])
        conditions.assert_not_called()
        representation.assert_not_called()
        save.assert_not_called()

    def test_first_condition_failure_stops_before_second_condition(self):
        result, conditions, representation, _, generated = self.exercise(
            condition_results=[{"passed": False}])
        self.assertFalse(result["passed"])
        self.assertEqual(result["stop_reason"], "stationary_condition_failed")
        self.assertEqual(conditions.call_count, 1)
        representation.assert_not_called()
        self.assertEqual(len(result["controls"]), 1)
        self.assertEqual(len(result["controls"][0]["conditions"]), 1)
        self.assertEqual({(pair, condition) for pair, condition, _, _ in generated},
                         {(0, 0)})

    def test_second_condition_failure_prevents_representation_and_next_pair(self):
        result, conditions, representation, _, generated = self.exercise(
            condition_results=[{"passed": True}, {"passed": False}])
        self.assertFalse(result["passed"])
        self.assertEqual(conditions.call_count, 2)
        representation.assert_not_called()
        self.assertEqual({pair for pair, _, _, _ in generated}, {0})
        self.assertEqual(len(result["controls"][0]["conditions"]), 2)

    def test_representation_failure_prevents_next_pair(self):
        result, conditions, representation, _, _ = self.exercise(
            representation_results=[{"passed": False}])
        self.assertFalse(result["passed"])
        self.assertEqual(result["stop_reason"], "representation_control_failed")
        self.assertEqual(conditions.call_count, 2)
        self.assertEqual(representation.call_count, 1)
        self.assertEqual(len(result["controls"]), 1)

    def test_complete_controls_stop_without_starting_later_stages(self):
        result, conditions, representation, save, generated = self.exercise()
        self.assertTrue(result["passed"])
        self.assertEqual(result["stop_reason"],
                         "authorized_controls_completed_await_user_decision")
        self.assertEqual(conditions.call_count, 6)
        self.assertEqual(representation.call_count, 3)
        self.assertEqual(save.call_count, 18)
        self.assertEqual([row["pair"] for row in result["controls"]], [0, 1, 2])
        self.assertTrue(all(row["passed"] for row in result["controls"]))
        for pair in range(3):
            for condition in (0, 1):
                self.assertEqual(
                    [(role, count) for p, c, role, count in generated
                     if (p, c) == (pair, condition)],
                    [("training", 40000), ("gate-calibration", 20000),
                     ("evaluation", 20000)])

    def test_numerical_error_propagates_without_automatic_retry(self):
        with self.assertRaisesRegex(ValueError, "fixture numerical failure"):
            self.exercise(data_error=ValueError("fixture numerical failure"))


if __name__ == "__main__":
    unittest.main()