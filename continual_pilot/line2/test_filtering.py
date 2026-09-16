"""Joint-filter mechanics using an artificial teacher, never the candidate pool."""
import copy
import unittest
from unittest.mock import patch

import numpy as np

from .filtering import JointMarginFilter, ProposalBudgetExceeded, score_margins


class ArtificialTeacher:
    """Simple deterministic score source, unrelated to experimental teachers."""

    def __init__(self):
        self.offsets = {0: np.zeros(4), 1: np.zeros(4)}
        self.weights = (np.full(4, 0.25), np.full(4, 0.25))
        self.means = np.zeros((4, 8), dtype=np.float64)
        self.w = np.eye(32, 8, dtype=np.float64)
        self.noise = 0.05

    def _base_scores(self, z, rule):
        value = z[:, rule]
        return np.column_stack((value, -value, value * 0, value * 0))


class FilteringTests(unittest.TestCase):
    def make_filter(self):
        z = np.zeros((20000, 8), dtype=np.float64)
        z[:, 0] = np.tile([-2.0, 2.0], 10000)
        z[:, 1] = np.tile([-4.0, 4.0], 10000)
        teacher = ArtificialTeacher()
        return JointMarginFilter(teacher, scale_latents=z), teacher, z

    def test_margin_is_top_two_difference_including_ties(self):
        scores = np.array([[1., 4., 2., 3.], [2., 2., -1., 0.],
                           [-4., -2., -3., -1.]])
        np.testing.assert_array_equal(score_margins(scores), [1., 0., 1.])

    def test_scales_are_population_std_of_unfiltered_scores(self):
        filtered, teacher, z = self.make_filter()
        expected = [teacher._base_scores(z, r).std(ddof=0) for r in (0, 1)]
        np.testing.assert_array_equal(filtered.scales, expected)
        self.assertFalse(filtered.scales.flags.writeable)

    def test_joint_threshold_includes_equality_not_one_rule_only(self):
        filtered, _, _ = self.make_filter()
        z = np.zeros((5, 8), dtype=np.float64)
        below = np.nextafter(0.1, 0.0)
        margins = np.array([
            [.1, .1], [.5, below], [below, .5], [.4, .4], [.0, .0]
        ])
        with patch.object(filtered, "normalized_margins", return_value=margins):
            np.testing.assert_array_equal(filtered.keep(z),
                                          [True, False, False, True, False])

    def test_teacher_copy_and_offsets_remain_unchanged(self):
        filtered, teacher, _ = self.make_filter()
        offsets = copy.deepcopy(filtered.teacher.offsets)
        scales = filtered.scales.copy()
        teacher.offsets[0][0] = 100
        filtered.sample_with_trace(16, 0, 0, np.random.default_rng(321))
        for rule in (0, 1):
            np.testing.assert_array_equal(filtered.teacher.offsets[rule], offsets[rule])
        np.testing.assert_array_equal(filtered.scales, scales)

    def test_selection_trace_preserves_order_and_full_precision(self):
        filtered, _, _ = self.make_filter()
        z, trace = filtered.accepted_latents(32, 0, np.random.default_rng(321))
        self.assertEqual(z.dtype, np.float64)
        self.assertEqual(len(z), 32)
        np.testing.assert_array_equal(z, trace["proposal_z"][trace["keep"]])
        np.testing.assert_array_equal(trace["accepted_proposal_indices"],
                                      np.flatnonzero(trace["keep"]))
        self.assertEqual(trace["proposed_count"], len(trace["proposal_z"]))
        self.assertTrue(filtered.keep(z).all())

    def test_budget_shortfall_raises_with_complete_trace(self):
        filtered, _, _ = self.make_filter()
        with patch.object(filtered, "keep",
                          side_effect=lambda z: np.zeros(len(z), dtype=bool)):
            with self.assertRaises(ProposalBudgetExceeded) as caught:
                filtered.accepted_latents(16, 0, np.random.default_rng(321),
                                          max_proposals=19)
        trace = caught.exception.trace
        self.assertEqual(trace["proposed_count"], 19)
        self.assertEqual(trace["accepted_count"], 0)
        self.assertEqual(trace["requested_count"], 16)
        self.assertEqual(len(trace["proposal_z"]), 19)
        self.assertFalse(trace["keep"].any())

    def test_sampling_reproducibility_and_noise_after_filtering(self):
        filtered, _, _ = self.make_filter()
        rng1, rng2 = np.random.default_rng(321), np.random.default_rng(321)
        first, trace = filtered.sample_with_trace(32, 1, 1, rng1)
        second, _ = filtered.sample_with_trace(32, 1, 1, rng2)
        for a, b in zip(first, second):
            np.testing.assert_array_equal(a, b)
        x, noisy, clean, z = first
        np.testing.assert_array_equal(clean, filtered.labels(z, 1))
        np.testing.assert_array_equal(x, (z @ filtered.teacher.w.T).astype(np.float32))
        rng3 = np.random.default_rng(321)
        expected_z, _ = filtered.accepted_latents(32, 1, rng3)
        flip = rng3.random(32) < filtered.teacher.noise
        offsets = rng3.integers(1, 4, size=32)
        np.testing.assert_array_equal(z, expected_z)
        np.testing.assert_array_equal(noisy, np.where(flip, (clean + offsets) % 4, clean))
        self.assertEqual(trace["accepted_count"], 32)

    def test_invalid_calibration_and_inputs_fail(self):
        filtered, teacher, z = self.make_filter()
        for bad in (z[:100], z.astype(np.float32), np.full_like(z, np.nan)):
            with self.assertRaises(ValueError):
                JointMarginFilter(teacher, scale_latents=bad)
        with self.assertRaises(ValueError):
            JointMarginFilter(teacher, scale_latents=np.zeros_like(z))
        with self.assertRaises(ValueError):
            filtered.scores(z[:1], 2)
        with self.assertRaises(ValueError):
            filtered.accepted_latents(0, 0, np.random.default_rng(0))
        with self.assertRaises(ValueError):
            filtered.proposals(1, 2, np.random.default_rng(0))


if __name__ == "__main__":
    unittest.main()