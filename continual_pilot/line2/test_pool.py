"""Control-pool orchestration tests; real candidate evaluation is mocked."""
import contextlib
import io
import unittest
from unittest.mock import Mock, patch

from .pool import candidate_seeds, run_control_pool


class PoolTests(unittest.TestCase):
    @staticmethod
    def decision(attempt, accepted=False):
        return {
            "teacher_seed": 10000 + attempt,
            "accepted": accepted,
            "reasons": [] if accepted else [
                {"mixture": 0, "criterion": "balance"},
                {"mixture": 1, "criterion": "balance"},
                {"mixture": 1, "criterion": "exclusion"},
            ],
        }

    def test_candidate_seeds_are_sequential_and_role_separated(self):
        all_seeds = []
        for attempt in range(200):
            seeds = candidate_seeds(attempt)
            self.assertEqual(seeds["teacher"], 10000 + attempt)
            self.assertEqual(seeds, candidate_seeds(attempt))
            all_seeds.extend([
                seeds["teacher"], seeds["offset"], seeds["scale"],
                *seeds["exclusion"], *seeds["acceptance"],
            ])
        self.assertEqual(len(all_seeds), len(set(all_seeds)))

    def test_invalid_candidate_index_fails(self):
        for attempt in (-1, 200, True, 1.0):
            with self.assertRaises(ValueError):
                candidate_seeds(attempt)

    def test_first_three_accepted_selected_without_further_evaluation(self):
        records = Mock()
        visited = []
        objects = {}

        def evaluate(_records, *, attempt):
            self.assertIs(_records, records)
            visited.append(attempt)
            objects[attempt] = object()
            return self.decision(attempt, attempt in (1, 3, 4)), objects[attempt]

        with patch("continual_pilot.line2.pool.evaluate_candidate", side_effect=evaluate):
            with contextlib.redirect_stdout(io.StringIO()):
                summary, accepted = run_control_pool(records)
        self.assertEqual(visited, [0, 1, 2, 3, 4])
        self.assertTrue(summary["accepted"])
        self.assertEqual(summary["attempts_tried"], 5)
        self.assertEqual(summary["rejected_count"], 2)
        self.assertEqual(summary["rejected_candidates_by_criterion"],
                         {"balance": 2, "exclusion": 2})
        self.assertEqual([item["pair"] for item in accepted], [0, 1, 2])
        self.assertEqual([item["teacher_seed"] for item in accepted],
                         [10001, 10003, 10004])
        for item, attempt in zip(accepted, (1, 3, 4)):
            self.assertIs(item["filtered"], objects[attempt])
        records.json.assert_called_once_with("acceptance_summary.json", summary)

    def test_cap_exhaustion_retains_partial_acceptances_and_stops(self):
        records = Mock()

        def evaluate(_records, *, attempt):
            return self.decision(attempt, attempt in (0, 199)), object()

        with patch("continual_pilot.line2.pool.evaluate_candidate",
                   side_effect=evaluate) as evaluator:
            with contextlib.redirect_stdout(io.StringIO()):
                summary, accepted = run_control_pool(records)
        self.assertEqual(evaluator.call_count, 200)
        self.assertFalse(summary["accepted"])
        self.assertEqual(summary["attempts_tried"], 200)
        self.assertEqual(summary["rejected_count"], 198)
        self.assertEqual(summary["next_action"], "stop_for_user_no_gate")
        self.assertEqual([item["teacher_seed"] for item in accepted], [10000, 10199])
        self.assertFalse(summary["learner_performance_used_for_selection"])

    def test_protocol_mismatch_prevents_candidate_evaluation(self):
        with patch("continual_pilot.line2.pool.verify_protocol",
                   side_effect=ValueError("Protocol mismatch")):
            with patch("continual_pilot.line2.pool.evaluate_candidate") as evaluator:
                with self.assertRaises(ValueError):
                    run_control_pool(Mock())
                evaluator.assert_not_called()

    def test_numerical_error_is_not_silently_rejected_or_retried(self):
        records = Mock()
        with patch("continual_pilot.line2.pool.evaluate_candidate",
                   side_effect=ValueError("Nonfinite teacher scale")) as evaluator:
            with self.assertRaises(ValueError):
                run_control_pool(records)
        self.assertEqual(evaluator.call_count, 1)
        records.json.assert_not_called()


if __name__ == "__main__":
    unittest.main()