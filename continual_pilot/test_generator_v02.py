"""Deterministic correctness tests for the v0.2 generator, not hypothesis tests."""
import unittest

import numpy as np
import torch

import generator_v02 as gv2


class GeneratorV02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_orthonormal_projection_and_shapes(self):
        g = gv2.GeneratorV02(seed=7, calibration_count=2000)
        np.testing.assert_allclose(g.w.T @ g.w, np.eye(8), atol=1e-12)
        x, noisy, clean, z = g.sample(100, 0, 0, np.random.default_rng(1))
        self.assertEqual(x.shape, (100, 32))
        self.assertEqual(z.shape, (100, 8))
        np.testing.assert_allclose(x @ g.w, z, atol=1e-5)

    def test_common_calibration_uses_real_mixture_not_standard_normal(self):
        # The common teacher scale must differ from a pilot-style N(0,1) scale,
        # because z[:, :2] is a mixture with means (+/-1, +/-1), not N(0,1).
        g = gv2.GeneratorV02(seed=7, calibration_count=20000)
        a, b, mixed_scale = g.teachers[0]
        rng = np.random.default_rng(123)
        normal = rng.normal(size=(20000, 2))
        raw = np.tanh(normal @ a) @ b
        centered = raw - raw.mean(axis=1, keepdims=True)
        normal_scale = float(centered.std())
        # Scales should be meaningfully different (mixture has larger spread).
        self.assertGreater(abs(mixed_scale - normal_scale) / normal_scale, 0.05)

    def test_mixed_z_draws_from_both_mixtures(self):
        g = gv2.GeneratorV02(seed=7, calibration_count=2000)
        z = g._mixed_z(np.random.default_rng(0), 4000)
        self.assertEqual(z.shape, (4000, 8))
        # First two dims are centered near component means (+/-1); overall mean
        # of |z[:, 0]| should be well above zero (mixture, not a spike at 0).
        self.assertGreater(np.mean(np.abs(z[:, 0])), 0.5)

    def test_label_noise_rate_matches_spec(self):
        g = gv2.GeneratorV02(seed=7, calibration_count=2000)
        _, noisy, clean, _ = g.sample(20000, 1, 1, np.random.default_rng(9))
        self.assertTrue(0.04 < np.mean(noisy != clean) < 0.06)
        self.assertTrue(np.all((noisy >= 0) & (noisy < 4)))

    def test_acceptance_metrics_shapes_and_bounds(self):
        g = gv2.GeneratorV02(seed=7, calibration_count=2000)
        metrics = gv2.acceptance_metrics(g, seed=3, count=4000)
        self.assertEqual(set(metrics["class_fractions"]),
                         {"M1_R1", "M1_R2", "M2_R1", "M2_R2"})
        for frac in metrics["class_fractions"].values():
            self.assertEqual(len(frac), 4)
            self.assertAlmostEqual(sum(frac), 1.0, places=5)
        self.assertEqual(set(metrics["disagreement"]), {"M1", "M2"})
        self.assertLessEqual(metrics["min_class_fraction"],
                             metrics["max_class_fraction"])

    def test_is_acceptable_boundary_logic(self):
        good = {
            "class_fractions": {"M1_R1": [0.25, 0.25, 0.25, 0.25]},
            "disagreement": {"M1": 0.5, "M2": 0.6},
        }
        self.assertTrue(gv2.is_acceptable(good))
        # A class fraction below the lower band fails.
        low = {
            "class_fractions": {"M1_R1": [0.10, 0.30, 0.30, 0.30]},
            "disagreement": {"M1": 0.5, "M2": 0.5},
        }
        self.assertFalse(gv2.is_acceptable(low))
        # A class fraction above the upper band fails.
        high = {
            "class_fractions": {"M1_R1": [0.40, 0.20, 0.20, 0.20]},
            "disagreement": {"M1": 0.5, "M2": 0.5},
        }
        self.assertFalse(gv2.is_acceptable(high))
        # Disagreement outside the band fails even if fractions are fine.
        bad_dis = {
            "class_fractions": {"M1_R1": [0.25, 0.25, 0.25, 0.25]},
            "disagreement": {"M1": 0.80, "M2": 0.50},
        }
        self.assertFalse(gv2.is_acceptable(bad_dis))

    def test_accept_generator_is_deterministic_and_takes_first(self):
        first, gen_a = gv2.accept_generator(
            alpha=0.5, noise=0.05, seed_start=1000, metric_seed=50000,
            calibration_count=3000)
        second, gen_b = gv2.accept_generator(
            alpha=0.5, noise=0.05, seed_start=1000, metric_seed=50000,
            calibration_count=3000)
        self.assertEqual(first["accepted"], second["accepted"])
        if first["accepted"]:
            # Deterministic: same accepted seed and same attempt count.
            self.assertEqual(first["accepted_seed"], second["accepted_seed"])
            self.assertEqual(first["attempts_tried"], second["attempts_tried"])
            # First acceptable is taken: the seed equals start + (attempts - 1).
            self.assertEqual(first["accepted_seed"],
                             1000 + first["attempts_tried"] - 1)
            # Every rejected seed genuinely fails the criterion.
            for entry in first["rejected_seeds"]:
                rejected = gv2.GeneratorV02(seed=entry["seed"], alpha=0.5,
                                            noise=0.05, calibration_count=3000)
                index = entry["seed"] - 1000
                metrics = gv2.acceptance_metrics(
                    rejected, seed=50000 + index, count=3000)
                self.assertFalse(gv2.is_acceptable(metrics))

    def test_max_attempts_failure_reports_design_failure(self):
        # An impossible criterion must fail cleanly without loosening.
        original_low, original_high = gv2.CLASS_LOW, gv2.CLASS_HIGH
        try:
            gv2.CLASS_LOW, gv2.CLASS_HIGH = 0.30, 0.31  # Impossible for 4 classes.
            saved_cap = gv2.MAX_ATTEMPTS
            gv2.MAX_ATTEMPTS = 5
            record, generator = gv2.accept_generator(
                alpha=0.5, noise=0.05, seed_start=1000, metric_seed=50000,
                calibration_count=2000)
            self.assertFalse(record["accepted"])
            self.assertIsNone(generator)
            self.assertEqual(record["attempts_tried"], 5)
            self.assertEqual(record["rejected_count"], 5)
        finally:
            gv2.CLASS_LOW, gv2.CLASS_HIGH = original_low, original_high
            gv2.MAX_ATTEMPTS = saved_cap


if __name__ == "__main__":
    unittest.main()