"""Small artificial-fixture tests; no generator, acceptance or gate runs."""
import copy
import io
import unittest

import numpy as np
import torch

from .config import derive_seed, verify_protocol
from .expert import Expert
from .memory import History, RecentKNN, ReplayMemory
from .router import Router


class PrimitiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.previous_threads)

    def assertTreeEqual(self, left, right):
        if isinstance(left, torch.Tensor):
            self.assertEqual(left.dtype, right.dtype)
            self.assertTrue(torch.equal(left, right))
        elif isinstance(left, np.ndarray):
            self.assertEqual(left.dtype, right.dtype)
            np.testing.assert_array_equal(left, right)
        elif isinstance(left, dict):
            self.assertEqual(left.keys(), right.keys())
            for key in left:
                self.assertTreeEqual(left[key], right[key])
        elif isinstance(left, (list, tuple)):
            self.assertEqual(len(left), len(right))
            for a, b in zip(left, right):
                self.assertTreeEqual(a, b)
        else:
            self.assertEqual(left, right)

    @staticmethod
    def fixture():
        rng = np.random.default_rng(123)
        return rng.normal(size=(16, 32)).astype(np.float32), np.arange(16) % 4

    def test_protocol_integrity(self):
        self.assertEqual(len(verify_protocol()), 64)

    def test_role_seeds_are_order_independent(self):
        a = derive_seed("mechanics-test", 0, "model0")
        derive_seed("control", 2, "training", phase=1)
        self.assertEqual(a, derive_seed("mechanics-test", 0, "model0"))
        self.assertNotEqual(a, derive_seed("mechanics-test", 0, "model1"))
        with self.assertRaises(ValueError):
            derive_seed("mechanics-test", -1, "model0")

    def test_initialization_is_paired_and_rng_isolated(self):
        before = torch.random.get_rng_state().clone()
        a = Expert(model_seed=7)
        c = Expert(model_seed=7, cpr_seed=9)
        Router()
        self.assertTreeEqual(a.model.state_dict(), c.model.state_dict())
        self.assertTrue(torch.equal(before, torch.random.get_rng_state()))

    def test_expert_scores_do_not_mutate_state(self):
        x, _ = self.fixture()
        expert = Expert(model_seed=7, cpr_seed=9)
        before = expert.state_dict()
        expert.scores(x)
        self.assertTreeEqual(before, expert.state_dict())

    def test_expert_checkpoint_continuation(self):
        x, y = self.fixture()
        expert = Expert(model_seed=7, cpr_seed=9)
        for _ in range(7):
            expert.update(x, y)
        with io.BytesIO() as stream:
            torch.save(expert.state_dict(), stream)
            stream.seek(0)
            restored = Expert.from_state_dict(torch.load(stream, weights_only=True))
        self.assertTreeEqual(expert.state_dict(), restored.state_dict())
        expert.update(x, y)
        restored.update(x, y)
        self.assertTreeEqual(expert.state_dict(), restored.state_dict())
        self.assertEqual(len(restored.cpr.events), 1)
        self.assertEqual(restored.cpr.events[0]["local_update"], 8)

    def test_cpr_uses_mean_of_individual_gradient_norms(self):
        x, y = self.fixture()
        expert = Expert(model_seed=7, cpr_seed=9)
        losses = torch.nn.functional.cross_entropy(
            expert.model(torch.from_numpy(x)), torch.from_numpy(y), reduction="none")
        gradients = torch.stack([
            torch.autograd.grad(loss, expert.model[0].weight, retain_graph=True)[0]
            for loss in losses
        ])
        expected = gradients.norm(dim=2).mean(dim=0)
        wrong = gradients.mean(dim=0).norm(dim=1)
        self.assertGreater(float((expected - wrong).abs().max()), 1e-5)
        actual = expert.cpr.observe(expert.model, losses)
        torch.testing.assert_close(actual, expected)
        torch.testing.assert_close(
            expert.cpr.utility, 0.99 + 0.01 * expected / (expected.mean() + 1e-8))
        self.assertTrue(all(p.grad is None for p in expert.model.parameters()))

    def test_cpr_preserves_bias_and_adam_moments(self):
        x, y = self.fixture()
        expert = Expert(model_seed=7, cpr_seed=9)
        for _ in range(7):
            expert.update(x, y)
        losses = torch.nn.functional.cross_entropy(
            expert.model(torch.from_numpy(x)), torch.from_numpy(y), reduction="none")
        expert.optimizer.zero_grad(set_to_none=True)
        expert.cpr.observe(expert.model, losses)
        losses.mean().backward()
        expert.optimizer.step()
        optimizer_before = copy.deepcopy(expert.optimizer.state_dict())
        biases = [expert.model[i].bias.detach().clone() for i in (0, 2)]
        event = expert.cpr.after_optimizer_step(expert.model)
        self.assertTreeEqual(optimizer_before, expert.optimizer.state_dict())
        for i, bias in zip((0, 2), biases):
            self.assertTrue(torch.equal(bias, expert.model[i].bias))
        self.assertTrue(torch.equal(expert.cpr.utility, torch.ones(64)))
        self.assertTrue(torch.all(event["fraction"] <= 0.01))
        torch.testing.assert_close(
            event["incoming_delta_norm"],
            (event["incoming_after"] - event["incoming_before"]).norm(dim=1))
        torch.testing.assert_close(
            event["outgoing_after"],
            event["outgoing_before"] * (1 - event["fraction"][None, :]))

    def test_cpr_activity_uses_supplied_phase_reference(self):
        x, y = self.fixture()
        expert = Expert(model_seed=7, cpr_seed=9)
        incoming = expert.model[0].weight.detach().clone()
        outgoing = expert.model[2].weight.detach().clone()
        for _ in range(16):
            expert.update(x, y)
        report = expert.cpr.activity(
            start_update=8, incoming_reference=incoming, outgoing_reference=outgoing)
        expected = expert.cpr.events[-1]["incoming_delta_norm"] / incoming.norm(dim=1)
        np.testing.assert_allclose(report["incoming_relative_path"], expected.numpy())
        self.assertEqual(report["intervention_count"], 1)

    def test_router_zero_ties_and_no_mutation(self):
        router = Router()
        summary = np.ones(132, dtype=np.float32)
        before = router.state_dict()
        self.assertEqual(router.greedy(summary), 0)
        self.assertTreeEqual(before, router.state_dict())
        result = router.update(summary, [2.0, 2.0])
        self.assertEqual(result["target_expert"], 0)

    def test_router_checkpoint_continuation(self):
        router = Router()
        summary = np.ones(132, dtype=np.float32)
        router.update(summary, [3.0, 1.0])
        restored = Router.from_state_dict(router.state_dict())
        router.update(summary, [1.0, 2.0])
        restored.update(summary, [1.0, 2.0])
        self.assertTreeEqual(router.state_dict(), restored.state_dict())

    def test_history_is_causal_and_rolls_over(self):
        history = History()
        self.assertTrue(np.all(history.summary() == 0))
        for i in range(65):
            history.observe(np.full(32, i, dtype=np.float32), i % 4)
        self.assertEqual(len(history.history), 64)
        np.testing.assert_array_equal(history.history[0][0], np.ones(32))
        before = history.state_dict()
        history.summary()
        self.assertTreeEqual(before, history.state_dict())
        restored = History()
        restored.load_state_dict(before)
        self.assertTreeEqual(before, restored.state_dict())

    def test_knn_empty_distance_ties_and_vote_ties(self):
        memory = RecentKNN()
        x = np.zeros(32, dtype=np.float32)
        self.assertEqual(memory.predict_one(x), 0)
        for label in (0, 0, 1, 1, 2, 2):
            memory.observe(x, label)
        # Five newest exclude the oldest zero; classes one and two tie.
        self.assertEqual(memory.predict_one(x), 1)
        before = memory.state_dict()
        memory.predict_one(x)
        self.assertTreeEqual(before, memory.state_dict())

    def test_reservoir_samples_only_observed_past(self):
        memory = ReplayMemory(replacement_seed=1, sampling_seed=2)
        x = np.zeros(32, dtype=np.float32)
        self.assertEqual(len(memory.sample(8)[1]), 0)
        memory.add(x, 3)
        old_x, old_y, indices = memory.sample(8)
        self.assertEqual(old_x.shape, (1, 32))
        np.testing.assert_array_equal(old_y, [3])
        np.testing.assert_array_equal(indices, [0])

    def test_reservoir_checkpoint_continuation_and_rng_separation(self):
        memory = ReplayMemory(replacement_seed=1, sampling_seed=2)
        for i in range(520):
            memory.add(np.full(32, i, dtype=np.float32), i % 4)
        restored = ReplayMemory(replacement_seed=99, sampling_seed=100)
        restored.load_state_dict(memory.state_dict())
        self.assertTreeEqual(memory.sample(8), restored.sample(8))
        replacement_before = copy.deepcopy(memory.replacement_rng.bit_generator.state)
        memory.sample(8)
        self.assertTreeEqual(replacement_before, memory.replacement_rng.bit_generator.state)

    def test_invalid_observations_and_labels_fail(self):
        history = History()
        for label in (4, -1, 1.5, True):
            with self.assertRaises(ValueError):
                history.observe(np.zeros(32), label)
        with self.assertRaises(ValueError):
            history.observe(np.full(32, np.nan), 0)


if __name__ == "__main__":
    unittest.main()