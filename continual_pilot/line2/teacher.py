"""Recorded v0.3-compatible base teacher for v0.4 joint filtering.

The explicit offset seed is a versioned sampling choice, not a claim of equality
with historical default-offset runs. No teacher is constructed on import.
"""
import copy

import numpy as np

from ..pilot import Generator
from .config import CALIBRATION_COUNT


OFFSET_ITERATIONS = 50
OFFSET_ETA = 0.5
OFFSET_TARGET = 0.25


class RecordedTeacher(Generator):
    """Preserve v0.3 arithmetic and draw order, while retaining calibration data."""

    def __init__(self, *, teacher_seed, offset_seed):
        self.teacher_seed = teacher_seed
        self.offset_seed = offset_seed
        self.alpha, self.noise = 0.5, 0.05
        rng = np.random.default_rng(teacher_seed)
        self.teacher_rng_before = copy.deepcopy(rng.bit_generator.state)
        self.w = np.linalg.qr(rng.normal(size=(32, 8)))[0]
        self.means = np.zeros((4, 8))
        self.means[:, :2] = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
        self.weights = (np.array([.4, .3, .2, .1]),
                        np.array([.1, .2, .3, .4]))
        raw_teachers = []
        for _ in range(3):
            a = rng.normal(size=(2, 16))
            b = rng.normal(size=(16, 4)) / 4
            raw_teachers.append((a, b))
        columns = ((0, 2), (2, 4), (4, 6))
        self.teachers = []
        self.component_calibrations = []
        for (a, b), (start, stop) in zip(raw_teachers, columns):
            full_z = self._mixed_z(rng, CALIBRATION_COUNT)
            self.component_calibrations.append(full_z)
            raw = np.tanh(full_z[:, start:stop] @ a) @ b
            centered = raw - raw.mean(axis=1, keepdims=True)
            scale = float(centered.std())
            if not np.isfinite(scale) or scale <= 0:
                raise ValueError("Nonpositive or nonfinite teacher component scale")
            self.teachers.append((a, b, scale))
        self.teacher_rng_after = copy.deepcopy(rng.bit_generator.state)

        offset_rng = np.random.default_rng(offset_seed)
        self.offset_rng_before = copy.deepcopy(offset_rng.bit_generator.state)
        self.offset_calibration = self._mixed_z(offset_rng, CALIBRATION_COUNT)
        self.offsets = {}
        self.offset_trajectories = {}
        for rule in (0, 1):
            base = self._base_scores(self.offset_calibration, rule)
            beta = np.zeros(4)
            trajectory = [beta.copy()]
            for _ in range(OFFSET_ITERATIONS):
                labels = (base + beta).argmax(axis=1)
                observed = np.bincount(labels, minlength=4) / CALIBRATION_COUNT
                safe = np.maximum(observed, 1.0 / CALIBRATION_COUNT)
                beta = beta + OFFSET_ETA * np.log(OFFSET_TARGET / safe)
                trajectory.append(beta.copy())
            if not np.isfinite(beta).all():
                raise ValueError("Nonfinite teacher offset")
            self.offsets[rule] = beta
            self.offset_trajectories[rule] = np.stack(trajectory)
        self.offset_rng_after = copy.deepcopy(offset_rng.bit_generator.state)

    def _mixed_z(self, rng, count):
        half = count // 2
        pieces = []
        for mixture, size in ((0, half), (1, count - half)):
            components = rng.choice(4, size=size, p=self.weights[mixture])
            pieces.append(rng.normal(size=(size, 8)) + self.means[components])
        return np.concatenate(pieces)

    def _base_scores(self, z, rule):
        common = self.component(z[:, :2], 0)
        specific = self.component(z[:, 2:4] if rule == 0 else z[:, 4:6], rule + 1)
        return self.alpha * common + specific

    def labels(self, z, rule):
        if type(rule) is not int or rule not in (0, 1):
            raise ValueError("Rule must be zero or one")
        return (self._base_scores(z, rule) + self.offsets[rule]).argmax(axis=1)

    def archive_arrays(self):
        """Return owned numerical arrays; writing them does not alter the teacher."""
        arrays = {
            "projection": self.w,
            "component_means": self.means,
            "mixture_weights": np.stack(self.weights),
            "offset_calibration_z": self.offset_calibration,
        }
        for index, (a, b, scale) in enumerate(self.teachers):
            arrays[f"teacher{index}_a"] = a
            arrays[f"teacher{index}_b"] = b
            arrays[f"teacher{index}_scale"] = np.asarray(scale, dtype=np.float64)
            arrays[f"teacher{index}_calibration_z"] = self.component_calibrations[index]
        for rule in (0, 1):
            arrays[f"rule{rule}_offset"] = self.offsets[rule]
            arrays[f"rule{rule}_offset_trajectory"] = self.offset_trajectories[rule]
        return {key: value.copy() for key, value in arrays.items()}

    def provenance(self):
        return copy.deepcopy({
            "version": "v04-base-v03-arithmetic-explicit-offset-seed",
            "teacher_seed": self.teacher_seed,
            "offset_seed": self.offset_seed,
            "alpha": self.alpha,
            "noise": self.noise,
            "component_calibration_count": CALIBRATION_COUNT,
            "offset_calibration_count": CALIBRATION_COUNT,
            "offset_iterations": OFFSET_ITERATIONS,
            "offset_eta": OFFSET_ETA,
            "offset_target": OFFSET_TARGET,
            "teacher_rng_before": self.teacher_rng_before,
            "teacher_rng_after": self.teacher_rng_after,
            "offset_rng_before": self.offset_rng_before,
            "offset_rng_after": self.offset_rng_after,
        })