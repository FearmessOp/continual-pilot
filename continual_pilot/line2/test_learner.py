"""Integration tests on artificial fixtures, not scientific pilot runs."""
import copy
import io
import unittest
from unittest.mock import patch

import numpy as np
import torch

from .learner import BASE_METHODS, BRANCH_RATES, Learner
from .schedule import cpr_event_count, window_schedule
from .test_primitives import PrimitiveTests


SEEDS = {
    "model0": 7, "model1": 8, "cpr0": 9, "cpr1": 10,
    "reservoir-replacement": 11, "reservoir-sampling": 12,
}


class LearnerTests(unittest.TestCase):
    assertTreeEqual = PrimitiveTests.assertTreeEqual

    @classmethod
    def setUpClass(cls):
        cls.previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.previous_threads)

    @staticmethod
    def fixture(count=32):
        rng = np.random.default_rng(456)
        return rng.normal(size=(count, 32)).astype(np.float32), np.arange(count) % 4

    def train(self, learner, count=32):
        x, y = self.fixture(count)
        predictions, groups = [], []
        for row, label in zip(x, y):
            predictions.append(learner.predict(row))
            result = learner.observe(label)
            if result["completed_group"] is not None:
                groups.append(result["completed_group"])
        return np.asarray(predictions), groups

    def test_handshake_all_methods(self):
        row = self.fixture()[0][0]
        for method in BASE_METHODS:
            with self.subTest(method=method):
                learner = Learner(method, seeds=SEEDS)
                with self.assertRaises(RuntimeError):
                    learner.observe(0)
                learner.predict(row)
                with self.assertRaises(RuntimeError):
                    learner.predict(row)
                with self.assertRaises(RuntimeError):
                    learner.checkpoint()
                learner.observe(0)
                with self.assertRaises(RuntimeError):
                    learner.frozen_predictions(row[None])

    def test_current_label_cannot_change_issued_prediction(self):
        row = self.fixture()[0][0]
        for method in BASE_METHODS:
            with self.subTest(method=method):
                left = Learner(method, seeds=SEEDS)
                right = left.fork()
                prediction = left.predict(row)
                self.assertEqual(prediction, right.predict(row))
                self.assertEqual(left.observe(0)["prediction"], prediction)
                self.assertEqual(right.observe(3)["prediction"], prediction)

    def test_group_selection_and_preupdate_loss_target(self):
        learner = Learner("B", seeds=SEEDS)
        x, y = self.fixture(16)
        initial_summary = learner.history.summary().copy()
        initial_experts = [e.state_dict() for e in learner.experts]
        losses = []
        for row, label in zip(x, y):
            scores = np.stack([e.scores(row[None])[0] for e in learner.experts])
            losses.append(torch.nn.functional.cross_entropy(
                torch.from_numpy(scores), torch.full((2,), int(label)),
                reduction="none").numpy())
            learner.predict(row)
            self.assertEqual(learner.group["selected"], 0)
            result = learner.observe(label)
        group = result["completed_group"]
        expected = np.stack(losses).mean(axis=0)
        self.assertEqual(group["router"]["target_expert"], int(expected.argmin()))
        np.testing.assert_array_equal(
            group["router"]["preupdate_mean_noisy_losses"], expected)
        np.testing.assert_array_equal(group["group_start_summary"], initial_summary)
        self.assertTreeEqual(initial_experts[1], learner.experts[1].state_dict())
        self.assertEqual(learner.experts[0].updates, 1)
        self.assertEqual(learner.router.updates, 1)

    def test_forced_exploration_and_local_cpr_clocks(self):
        learner = Learner("D", seeds=SEEDS)
        with patch.object(learner.router, "greedy", return_value=0):
            _, groups = self.train(learner, 16 * 16)
        forced = [(g["global_group"], g["forced_expert"])
                  for g in groups if g["forced_expert"] is not None]
        self.assertEqual(forced, [(8, 0), (16, 1)])
        self.assertEqual([e.updates for e in learner.experts], [15, 1])
        self.assertEqual([e.cpr.local_updates for e in learner.experts], [15, 1])
        self.assertEqual([len(e.cpr.events) for e in learner.experts], [1, 0])
        self.assertEqual(learner.forced_groups, [1, 1])
        self.assertEqual(learner.greedy_groups, [14, 0])

    def test_checkpoint_roundtrip_and_continuation_all_methods(self):
        for method in BASE_METHODS:
            with self.subTest(method=method):
                learner = Learner(method, seeds=SEEDS)
                self.train(learner, 16)
                with io.BytesIO() as stream:
                    torch.save(learner.checkpoint(), stream)
                    stream.seek(0)
                    restored = Learner.from_checkpoint(
                        torch.load(stream, weights_only=True))
                self.assertTreeEqual(learner.checkpoint(), restored.checkpoint())
                predictions, groups = self.train(learner, 16)
                other_predictions, other_groups = self.train(restored, 16)
                self.assertTreeEqual(predictions, other_predictions)
                self.assertTreeEqual(groups, other_groups)
                self.assertTreeEqual(learner.checkpoint(), restored.checkpoint())

    def test_frozen_order_invariance_and_state_preservation(self):
        x, _ = self.fixture()
        for method in BASE_METHODS:
            with self.subTest(method=method):
                learner = Learner(method, seeds=SEEDS)
                self.train(learner)
                before = learner.checkpoint()
                prediction = learner.frozen_predictions(x)
                reversed_prediction = learner.frozen_predictions(x[::-1])
                np.testing.assert_array_equal(prediction, reversed_prediction[::-1])
                self.assertTreeEqual(before, learner.checkpoint())

    def test_sparse_branches_preserve_optimizer_and_discard_skipped_groups(self):
        parent = Learner("A", seeds=SEEDS)
        self.train(parent, 16)
        before = parent.checkpoint()
        for name, expected_steps in (
                ("sparse25", 1), ("sparse50", 2), ("sparse75", 3), ("frozen-F2", 0)):
            with self.subTest(method=name):
                child = parent.branch_from_a(name)
                self.assertTreeEqual(parent.experts[0].state_dict(),
                                     child.experts[0].state_dict())
                # Groups 2 through 5: exact schedule; no warmup experiment.
                _, groups = self.train(child, 64)
                self.assertEqual(sum(g["expert_updated"] for g in groups), expected_steps)
                self.assertEqual(child.experts[0].updates, 1 + expected_steps)
                self.assertEqual(child.experts[0].training_examples,
                                 16 * (1 + expected_steps))
                self.assertTreeEqual(before, parent.checkpoint())
                restored = Learner.from_checkpoint(child.checkpoint())
                self.assertTreeEqual(child.checkpoint(), restored.checkpoint())

    def test_skipped_group_leaves_expert_and_moments_unchanged(self):
        parent = Learner("A", seeds=SEEDS)
        self.train(parent, 32)
        child = parent.branch_from_a("sparse25")
        before = child.experts[0].state_dict()
        self.train(child, 16)  # Global group 3 is discarded.
        self.assertTreeEqual(before, child.experts[0].state_dict())

    def test_frozen_reference_online_difference_is_zero(self):
        parent = Learner("A", seeds=SEEDS)
        self.train(parent, 16)
        frozen = parent.branch_from_a("frozen-F2")
        x, clean_fixture = self.fixture(480)
        reference = parent.frozen_predictions(x)
        state = frozen.experts[0].state_dict()
        history = frozen.history.state_dict()
        online, _ = self.train(frozen, 480)
        np.testing.assert_array_equal(online, reference)
        difference = (online != clean_fixture).sum() - (reference != clean_fixture).sum()
        self.assertEqual(difference, 0)
        self.assertTreeEqual(state, frozen.experts[0].state_dict())
        self.assertTreeEqual(history, frozen.history.state_dict())

    def test_replay_indices_are_past_only_and_reporting_is_read_only(self):
        learner = Learner("replay", seeds=SEEDS)
        twin = learner.fork()
        x, y = self.fixture(32)
        for index, (row, label) in enumerate(zip(x, y)):
            self.assertEqual(learner.predict(row), twin.predict(row))
            report = learner.observe(label)
            twin.observe(label)
            indices = report["sampled_replay_indices"]
            self.assertTrue(np.all(indices < index))
            self.assertTrue(np.all(indices >= 0))
            # An evaluator may alter its returned copy, never the training memory.
            indices.fill(-999)
            if report["completed_group"] is not None:
                self.assertTreeEqual(learner.checkpoint(), twin.checkpoint())
        self.assertEqual(learner.maximum_training_batch, 144)

    def test_protocol_phase_windows_without_training(self):
        phase3_start = 50000
        phase4_start = phase3_start + 1024
        for rate, phase3_updates, phase4_updates in (
                (25, 16, 7), (50, 32, 15), (75, 48, 23), (100, 64, 30)):
            self.assertEqual(window_schedule(
                phase3_start, 1024, rate_percent=rate)["actual_updates"], phase3_updates)
            report = window_schedule(phase4_start, 480, rate_percent=rate)
            self.assertEqual(report["actual_updates"], phase4_updates)
            self.assertEqual(report["exploration_groups"], [3192, 3200, 3208, 3216])
            self.assertEqual(report["included_count"], 416)
            self.assertEqual(report["excluded_count"], 64)
        self.assertEqual(cpr_event_count(7, 1), 1)
        self.assertEqual(cpr_event_count(8, 7), 0)
        self.assertEqual(cpr_event_count(3125, 64), 8)

    def test_branching_restrictions(self):
        for method in BRANCH_RATES:
            with self.assertRaises(ValueError):
                Learner(method, seeds=SEEDS)
        with self.assertRaises(ValueError):
            Learner("B", seeds=SEEDS).branch_from_a("sparse25")


if __name__ == "__main__":
    unittest.main()