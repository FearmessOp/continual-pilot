"""Data-provenance tests using an artificial teacher, never the candidate pool."""
import unittest

import numpy as np

from .data import learner_seeds, representation_data, stationary_data
from .filtering import JointMarginFilter
from .records import tree_digest
from .test_filtering import ArtificialTeacher


class DataTests(unittest.TestCase):
    @staticmethod
    def filtered():
        z = np.zeros((20000, 8), dtype=np.float64)
        z[:, 0] = np.tile([-2.0, 2.0], 10000)
        z[:, 1] = np.tile([-4.0, 4.0], 10000)
        return JointMarginFilter(ArtificialTeacher(), scale_latents=z)

    def test_learner_seeds_are_method_independent_and_distinct(self):
        first = learner_seeds("mechanics-test", 0)
        self.assertEqual(first, learner_seeds("mechanics-test", 0))
        self.assertEqual(len(set(first.values())), len(first))
        other = learner_seeds("mechanics-test", 1)
        self.assertTrue(set(first.values()).isdisjoint(other.values()))

    def test_stationary_roles_and_conditions_use_distinct_streams(self):
        filtered = self.filtered()
        seeds = []
        for role in ("training", "gate-calibration", "evaluation", "mapping"):
            for condition in (0, 1):
                result = stationary_data(
                    filtered, section="mechanics-test", pair=0, role=role,
                    condition=condition, count=16)
                seeds.append(result["provenance"]["seed"])
                data = result["arrays"]
                np.testing.assert_array_equal(
                    data["clean"], data[f"r{condition + 1}"])
                np.testing.assert_array_equal(data["index"], np.arange(16))
                self.assertEqual(data["z"].dtype, np.float64)
        self.assertEqual(len(set(seeds)), 8)

    def test_stationary_rng_checkpoint_recreates_data(self):
        filtered = self.filtered()
        result = stationary_data(
            filtered, section="mechanics-test", pair=0, role="training",
            condition=1, count=32)
        rng = np.random.default_rng()
        rng.bit_generator.state = result["provenance"]["rng_before"]
        values, trace = filtered.sample_with_trace(32, 1, 1, rng)
        for key, value in zip(("x", "noisy", "clean", "z"), values):
            np.testing.assert_array_equal(result["arrays"][key], value)
        self.assertEqual(tree_digest(trace), tree_digest(result["trace"]))
        self.assertEqual(tree_digest(rng.bit_generator.state),
                         tree_digest(result["provenance"]["rng_after"]))

    def test_representation_splits_have_independent_seed_namespaces(self):
        filtered = self.filtered()
        train = representation_data(
            filtered, section="mechanics-test", pair=0, split="train")
        test = representation_data(
            filtered, section="mechanics-test", pair=0, split="test")
        self.assertTrue(set(train["provenance"]["seeds"].values()).isdisjoint(
            test["provenance"]["seeds"].values()))
        self.assertFalse(np.array_equal(train["arrays"]["z"], test["arrays"]["z"]))
        repeated = representation_data(
            filtered, section="mechanics-test", pair=0, split="train")
        self.assertEqual(tree_digest(train), tree_digest(repeated))

    def test_representation_shared_inputs_and_separate_noise_reproduce(self):
        filtered = self.filtered()
        result = representation_data(
            filtered, section="mechanics-test", pair=1, split="test")
        data, provenance = result["arrays"], result["provenance"]
        self.assertEqual(data["x"].shape, (32768, 32))
        np.testing.assert_array_equal(
            data["x"], (data["z"] @ filtered.teacher.w.T).astype(np.float32))
        for rule in (0, 1):
            name = f"noise_r{rule + 1}"
            clean = filtered.labels(data["z"], rule)
            np.testing.assert_array_equal(data["clean_by_rule"][:, rule], clean)
            rng = np.random.default_rng()
            rng.bit_generator.state = provenance["rng_before"][name]
            flip = rng.random(len(clean)) < filtered.teacher.noise
            offsets = rng.integers(1, 4, size=len(clean))
            expected = np.where(flip, (clean + offsets) % 4, clean)
            np.testing.assert_array_equal(data["noisy_by_rule"][:, rule], expected)
            self.assertEqual(tree_digest(rng.bit_generator.state),
                             tree_digest(provenance["rng_after"][name]))

    def test_invalid_roles_conditions_and_splits_fail_before_sampling(self):
        filtered = self.filtered()
        for role, condition in (("acceptance", 0), ("training", 2), ("training", True)):
            with self.assertRaises(ValueError):
                stationary_data(
                    filtered, section="mechanics-test", pair=0,
                    role=role, condition=condition, count=16)
        with self.assertRaises(ValueError):
            representation_data(
                filtered, section="mechanics-test", pair=0, split="validation")


if __name__ == "__main__":
    unittest.main()