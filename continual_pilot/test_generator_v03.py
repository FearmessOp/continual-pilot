"""Deterministic correctness tests for the v0.3 generator, not hypothesis tests."""
import unittest

import numpy as np
import torch

import generator_v03 as gv3


class GeneratorV03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_orthonormal_projection_and_shapes(self):
        g = gv3.GeneratorV03(seed=7, calibration_count=2000)
        np.testing.assert_allclose(g.w.T @ g.w, np.eye(8), atol=1e-12)
        x, noisy, clean, z = g.sample(100, 0, 0, np.random.default_rng(1))
        self.assertEqual(x.shape, (100, 32))
        self.assertEqual(z.shape, (100, 8))
        np.testing.assert_allclose(x @ g.w, z, atol=1e-5)

    def test_offset_shape_and_recomputed_per_seed(self):
        g7 = gv3.GeneratorV03(seed=7, calibration_count=2000)
        g8 = gv3.GeneratorV03(seed=8, calibration_count=2000)
        self.assertEqual(set(g7.offsets), {0, 1})
        for rule in (0, 1):
            self.assertEqual(g7.offsets[rule].shape, (4,))
            # Teacher-dependent: different seeds give different offsets.
            self.assertFalse(np.allclose(g7.offsets[rule], g8.offsets[rule]))

    def test_offset_reduces_mixed_marginal_toward_quarter(self):
        # Mechanical verification (NOT acceptance): the offset must pull the
        # mixed-marginal class fractions to within +/- 2% of 1/4 per rule.
        g = gv3.GeneratorV03(seed=7, calibration_count=20000)
        mixed = g.mixed_marginal_fractions(seed=999, count=20000)
        for rule in ("R1", "R2"):
            fractions = np.array(mixed[rule])
            self.assertAlmostEqual(float(fractions.sum()), 1.0, places=5)
            worst = float(np.max(np.abs(fractions - gv3.OFFSET_TARGET)))
            self.assertLessEqual(worst, gv3.MECHANICAL_TOLERANCE,
                                 f"{rule} off by {worst:.4f}")

    def test_offset_calibration_seed_is_independent(self):
        # The offset uses its own RNG stream; drawing a sample with a shared
        # numpy default generator must not change the calibrated offsets.
        first = gv3.GeneratorV03(seed=7, calibration_count=2000)
        np.random.default_rng(7).normal(size=(5000, 8))  # Unrelated draw.
        second = gv3.GeneratorV03(seed=7, calibration_count=2000)
        for rule in (0, 1):
            np.testing.assert_allclose(first.offsets[rule],
                                       second.offsets[rule], atol=1e-12)

    def test_label_noise_rate_matches_spec(self):
        g = gv3.GeneratorV03(seed=7, calibration_count=2000)
        _, noisy, clean, _ = g.sample(20000, 1, 1, np.random.default_rng(9))
        self.assertTrue(0.04 < np.mean(noisy != clean) < 0.06)
        self.assertTrue(np.all((noisy >= 0) & (noisy < 4)))

    def test_common_specific_structure_preserved(self):
        # Offset is purely additive on the scores; removing it must equal the
        # pilot-style additive common+specific argmax.
        g = gv3.GeneratorV03(seed=7, calibration_count=2000)
        rng = np.random.default_rng(3)
        _, _, _, z = g.sample(500, 0, 0, rng)
        base = g._base_scores(z, 0)
        with_offset = (base + g.offsets[0]).argmax(axis=1)
        np.testing.assert_array_equal(with_offset, g.labels(z, 0))
        # The base scores are exactly alpha*common + specific (no offset).
        common = g.component(z[:, :2], 0)
        specific = g.component(z[:, 2:4], 1)
        np.testing.assert_allclose(base, g.alpha * common + specific, atol=1e-6)

    def test_acceptance_metrics_shapes(self):
        g = gv3.GeneratorV03(seed=7, calibration_count=2000)
        metrics = gv3.acceptance_metrics(g, seed=3, count=4000)
        self.assertEqual(set(metrics["class_fractions"]),
                         {"M1_R1", "M1_R2", "M2_R1", "M2_R2"})
        for frac in metrics["class_fractions"].values():
            self.assertEqual(len(frac), 4)
            self.assertAlmostEqual(sum(frac), 1.0, places=5)
        self.assertEqual(set(metrics["disagreement"]), {"M1", "M2"})

    def test_failure_reason_classification(self):
        balanced = {"class_fractions": {"M1_R1": [0.25, 0.25, 0.25, 0.25]},
                    "disagreement": {"M1": 0.5, "M2": 0.6}}
        self.assertEqual(gv3.failure_reason(balanced), [])
        self.assertTrue(gv3.is_acceptable(balanced))
        only_balance = {"class_fractions": {"M1_R1": [0.10, 0.30, 0.30, 0.30]},
                        "disagreement": {"M1": 0.5, "M2": 0.5}}
        self.assertEqual(gv3.failure_reason(only_balance), ["balance"])
        only_dis = {"class_fractions": {"M1_R1": [0.25, 0.25, 0.25, 0.25]},
                    "disagreement": {"M1": 0.80, "M2": 0.5}}
        self.assertEqual(gv3.failure_reason(only_dis), ["disagreement"])
        both = {"class_fractions": {"M1_R1": [0.10, 0.30, 0.30, 0.30]},
                "disagreement": {"M1": 0.80, "M2": 0.5}}
        self.assertEqual(gv3.failure_reason(both), ["balance", "disagreement"])

    def test_accept_generator_is_deterministic_and_counts_reasons(self):
        first, gen_a = gv3.accept_generator(
            alpha=0.5, noise=0.05, seed_start=1000, metric_seed=50000,
            calibration_count=3000)
        second, gen_b = gv3.accept_generator(
            alpha=0.5, noise=0.05, seed_start=1000, metric_seed=50000,
            calibration_count=3000)
        self.assertEqual(first["accepted"], second["accepted"])
        by = first["rejected_by_reason"]
        self.assertEqual(set(by), {"balance_only", "disagreement_only", "both"})
        self.assertEqual(sum(by.values()), first["rejected_count"])
        if first["accepted"]:
            self.assertEqual(first["accepted_seed"], second["accepted_seed"])
            self.assertEqual(first["accepted_seed"],
                             1000 + first["attempts_tried"] - 1)
            # Accepted generator reports mixed marginals as verification.
            self.assertIn("accepted_mixed_marginals", first)

    def test_max_attempts_failure_reports_decision_tree(self):
        original_low, original_high = gv3.CLASS_LOW, gv3.CLASS_HIGH
        saved_cap = gv3.MAX_ATTEMPTS
        try:
            gv3.CLASS_LOW, gv3.CLASS_HIGH = 0.30, 0.31  # Impossible.
            gv3.MAX_ATTEMPTS = 4
            record, generator = gv3.accept_generator(
                alpha=0.5, noise=0.05, seed_start=1000, metric_seed=50000,
                calibration_count=2000)
            self.assertFalse(record["accepted"])
            self.assertIsNone(generator)
            self.assertEqual(record["attempts_tried"], 4)
            self.assertIn("decision_tree", record)
        finally:
            gv3.CLASS_LOW, gv3.CLASS_HIGH = original_low, original_high
            gv3.MAX_ATTEMPTS = saved_cap


if __name__ == "__main__":
    unittest.main()