"""Base-teacher parity tests outside all experimental candidate pools."""
import importlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from .records import tree_digest
from .teacher import RecordedTeacher


class TeacherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Legacy imports use top-level module names. Import only definitions;
        # its guarded CLI is never invoked, and restore the module search path.
        project = str(Path(__file__).resolve().parents[1])
        with patch.object(sys, "path", [project, *sys.path]):
            legacy = importlib.import_module("generator_v03")
        cls.legacy = legacy.GeneratorV03(seed=7, offset_seed=90007)
        cls.recorded = RecordedTeacher(teacher_seed=7, offset_seed=90007)

    def test_weights_scales_offsets_match_legacy_exactly(self):
        old, new = self.legacy, self.recorded
        np.testing.assert_array_equal(old.w, new.w)
        np.testing.assert_array_equal(old.means, new.means)
        for old_weights, new_weights in zip(old.weights, new.weights):
            np.testing.assert_array_equal(old_weights, new_weights)
        for old_teacher, new_teacher in zip(old.teachers, new.teachers):
            for expected, actual in zip(old_teacher, new_teacher):
                np.testing.assert_array_equal(expected, actual)
        for rule in (0, 1):
            np.testing.assert_array_equal(old.offsets[rule], new.offsets[rule])

    def test_all_mixture_rule_samples_and_rng_states_match(self):
        for mixture in (0, 1):
            for rule in (0, 1):
                with self.subTest(mixture=mixture, rule=rule):
                    old_rng = np.random.default_rng(17)
                    new_rng = np.random.default_rng(17)
                    expected = self.legacy.sample(32, mixture, rule, old_rng)
                    actual = self.recorded.sample(32, mixture, rule, new_rng)
                    for left, right in zip(expected, actual):
                        self.assertEqual(left.dtype, right.dtype)
                        self.assertEqual(left.tobytes(), right.tobytes())
                    self.assertEqual(tree_digest(old_rng.bit_generator.state),
                                     tree_digest(new_rng.bit_generator.state))

    def test_calibration_and_offset_trajectory_are_reconstructible(self):
        teacher = self.recorded
        for index, (a, b, scale) in enumerate(teacher.teachers):
            z = teacher.component_calibrations[index]
            self.assertEqual(z.shape, (20000, 8))
            self.assertEqual(z.dtype, np.float64)
            raw = np.tanh(z[:, 2 * index:2 * index + 2] @ a) @ b
            self.assertEqual(float((raw - raw.mean(axis=1, keepdims=True)).std()),
                             scale)
        for rule in (0, 1):
            trajectory = teacher.offset_trajectories[rule]
            self.assertEqual(trajectory.shape, (51, 4))
            np.testing.assert_array_equal(trajectory[0], np.zeros(4))
            base = teacher._base_scores(teacher.offset_calibration, rule)
            for step in range(50):
                labels = (base + trajectory[step]).argmax(axis=1)
                observed = np.bincount(labels, minlength=4) / 20000
                expected = trajectory[step] + .5 * np.log(
                    .25 / np.maximum(observed, 1 / 20000))
                np.testing.assert_array_equal(trajectory[step + 1], expected)
            np.testing.assert_array_equal(trajectory[-1], teacher.offsets[rule])

    def test_archives_are_owned_copies_and_provenance_is_explicit(self):
        teacher = self.recorded
        before = tree_digest(teacher.archive_arrays())
        arrays = teacher.archive_arrays()
        arrays["projection"].fill(0)
        arrays["rule0_offset"].fill(99)
        self.assertEqual(before, tree_digest(teacher.archive_arrays()))
        provenance = teacher.provenance()
        self.assertEqual(provenance["teacher_seed"], 7)
        self.assertEqual(provenance["offset_seed"], 90007)
        provenance["teacher_rng_before"].clear()
        self.assertTrue(teacher.provenance()["teacher_rng_before"])


if __name__ == "__main__":
    unittest.main()