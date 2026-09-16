"""Small deterministic correctness tests, not scientific hypothesis tests."""
import copy
import unittest
from types import SimpleNamespace

import numpy as np
import torch

from pilot import Context, Generator, Reservoir, evaluate, make_model, run


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.generator = Generator(seed=11)

    def args(self):
        return SimpleNamespace(lr=.001, context_window=4, capacity=5,
                               seed=11, replay_batch=2, hidden=8)

    def test_invertible_observation_and_orthogonality(self):
        g = self.generator
        np.testing.assert_allclose(g.w.T @ g.w, np.eye(8), atol=1e-12)
        x, _, _, z = g.sample(100, 0, 0, np.random.default_rng(42))
        np.testing.assert_allclose(x @ g.w, z, atol=1e-6)

    def test_noise_and_clean_rule(self):
        x, y, clean, z = self.generator.sample(
            20000, 1, 1, np.random.default_rng(42))
        np.testing.assert_array_equal(clean, self.generator.labels(z, 1))
        self.assertTrue(.04 < np.mean(y != clean) < .06)
        self.assertEqual(x.dtype, np.float32)
        self.assertTrue(np.all((y >= 0) & (y < 4)))

    def test_stream_reproducibility_and_phase_rules(self):
        g = self.generator
        first = g.stream(20, 42)
        second = g.stream(20, 42)
        for left, right in zip(first, second):
            np.testing.assert_array_equal(left, right)
        x, _, clean = first
        z = x @ g.w
        for phase, rule in enumerate((0, 0, 1, 0)):
            region = slice(phase * 20, (phase + 1) * 20)
            np.testing.assert_array_equal(clean[region], g.labels(z[region], rule))

    def test_context_only_contains_past_and_expires(self):
        context = Context(window=2)
        x = np.ones(32, dtype=np.float32)
        encoded = context.encode(x)
        np.testing.assert_array_equal(encoded[32:], 0)
        context.observe(x, 1)
        after = context.encode(x)
        self.assertEqual(after[33], 1)
        np.testing.assert_array_equal(encoded[32:], 0)
        context.observe(x * 2, 2)
        context.observe(x * 3, 2)
        result = context.encode(x)
        self.assertEqual(result[33], 0)
        self.assertEqual(result[34], 1)
        np.testing.assert_allclose(result[36:].reshape(4, 32)[2], 2.5)

    def test_reservoir_capacity_copy_and_sampling(self):
        buffer = Reservoir(3, 2, seed=8)
        self.assertEqual(len(buffer.sample(2)[1]), 0)
        x = np.array([1, 2], dtype=np.float32)
        buffer.add(x, 2)
        x[:] = 99
        np.testing.assert_array_equal(buffer.sample(1)[0], [[1, 2]])
        for i in range(1, 100):
            buffer.add(np.array([i, i], dtype=np.float32), i)
        self.assertEqual(buffer.seen, 100)
        self.assertEqual(buffer.x.shape, (3, 2))
        self.assertEqual(len(buffer.sample(10)[1]), 3)

    def test_current_and_future_labels_do_not_affect_current_prediction(self):
        args = self.args()
        torch.manual_seed(123)
        initial = make_model(args.hidden)
        original = self.generator.stream(8, 51, health=True)
        changed = tuple(array.copy() for array in original)
        changed[1][4:] = (changed[1][4:] + 1) % 4
        state_before = copy.deepcopy(initial.state_dict())
        for replay in (False, True):
            left = run(initial, original, args, replay)
            right = run(initial, changed, args, replay)
            np.testing.assert_array_equal(left["predictions"][:5],
                                          right["predictions"][:5])
            expected = 8 + (sum(min(t, 2) for t in range(8)) if replay else 0)
            self.assertEqual(left["training_examples_including_replay"], expected)
            self.assertEqual(left["optimizer_steps"], 8)
        for name, tensor in initial.state_dict().items():
            self.assertTrue(torch.equal(tensor, state_before[name]))

    def test_oracle_regret_and_partial_blocks(self):
        stream = (np.zeros((6, 32)), np.array([0, 1, 2, 0, 1, 2]),
                  np.array([0, 1, 2, 0, 1, 3]))
        result = {"predictions": stream[2].copy()}
        rows = evaluate(result, stream, phase_length=3, block_size=2)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["regret"] == 0 for row in rows))
        self.assertEqual(sum(row["count"] for row in rows), 6)
        self.assertEqual(result["phases"][1]["first_window_size"], 3)


if __name__ == "__main__":
    unittest.main()