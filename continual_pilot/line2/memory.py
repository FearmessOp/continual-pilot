"""Causal memories with portable state; no clean labels or regime metadata."""
import copy
from collections import deque

import numpy as np
import torch

from ..pilot import Context
from .config import (
    CLASSES, CONTEXT_WINDOW, INPUT_DIM, KNN_NEIGHBORS, KNN_WINDOW,
    REPLAY_CAPACITY,
)


def observation(x, y=None):
    """Own a finite observation; reject malformed labels rather than truncate."""
    value = np.asarray(x, dtype=np.float32)
    if value.shape != (INPUT_DIM,) or not np.isfinite(value).all():
        raise ValueError("Expected one finite 32-dimensional observation")
    if y is not None:
        if isinstance(y, (bool, np.bool_)) or not isinstance(y, (int, np.integer)):
            raise ValueError("Observed label must be an integer")
        if not 0 <= y < CLASSES:
            raise ValueError("Observed label outside class range")
    return value.copy()


class History(Context):
    """Same arithmetic as historical context, with explicit checkpoint state."""

    def __init__(self):
        super().__init__(CONTEXT_WINDOW)

    def summary(self):
        return self.encode(np.zeros(INPUT_DIM, dtype=np.float32))[INPUT_DIM:]

    def observe(self, x, y):
        super().observe(observation(x, y), int(y))

    def state_dict(self):
        return {
            "window": self.window,
            "history": [(torch.from_numpy(x.copy()), y) for x, y in self.history],
            "sums": torch.from_numpy(self.sums.copy()),
            "counts": torch.from_numpy(self.counts.copy()),
        }

    def load_state_dict(self, state):
        if state["window"] != CONTEXT_WINDOW:
            raise ValueError("Checkpoint context window differs from protocol")
        if len(state["history"]) > CONTEXT_WINDOW:
            raise ValueError("Checkpoint history exceeds window")
        history = deque(
            (observation(x.cpu().numpy(), y), int(y)) for x, y in state["history"])
        counts = state["counts"].cpu().numpy().copy()
        expected = np.bincount([y for _, y in history], minlength=CLASSES)
        sums = state["sums"].cpu().numpy().copy()
        if not np.array_equal(counts, expected):
            raise ValueError("Checkpoint context counts disagree with history")
        if sums.shape != (CLASSES, INPUT_DIM) or not np.isfinite(sums).all():
            raise ValueError("Invalid context sums")
        # Preserve accumulated float32 rounding; recomputation changes state.
        self.history, self.counts, self.sums = history, counts, sums


class RecentKNN:
    """Raw-distance kNN; newest wins distance ties, lowest class wins vote ties."""

    def __init__(self):
        self.history = deque(maxlen=KNN_WINDOW)

    def predict_one(self, x):
        x = observation(x)
        if not self.history:
            return 0
        stored = np.stack([row for row, _ in self.history]).astype(np.float64)
        squared = np.sum((stored - x.astype(np.float64)) ** 2, axis=1)
        indices = np.arange(len(self.history), dtype=np.int64)
        nearest = np.lexsort((-indices, squared))[:KNN_NEIGHBORS]
        labels = np.asarray([y for _, y in self.history], dtype=np.int64)
        return int(np.bincount(labels[nearest], minlength=CLASSES).argmax())

    def observe(self, x, y):
        self.history.append((observation(x, y), int(y)))

    def state_dict(self):
        return {
            "history": [(torch.from_numpy(x.copy()), y) for x, y in self.history]
        }

    def load_state_dict(self, state):
        if len(state["history"]) > KNN_WINDOW:
            raise ValueError("Checkpoint kNN history exceeds window")
        self.history = deque(
            ((observation(x.cpu().numpy(), y), int(y))
             for x, y in state["history"]), maxlen=KNN_WINDOW)


class ReplayMemory:
    """Uniform reservoir with independent replacement and sampling streams.

    Indices identify past observations for an external evaluator. They never
    affect sampling or the training features/targets. Call sample before add.
    """

    def __init__(self, *, replacement_seed, sampling_seed):
        self.x = np.zeros((REPLAY_CAPACITY, INPUT_DIM), dtype=np.float32)
        self.y = np.zeros(REPLAY_CAPACITY, dtype=np.int64)
        self.indices = np.full(REPLAY_CAPACITY, -1, dtype=np.int64)
        self.seen = 0
        self.replacement_rng = np.random.default_rng(replacement_seed)
        self.sampling_rng = np.random.default_rng(sampling_seed)

    def sample(self, count):
        if type(count) is not int or count < 0:
            raise ValueError("Sample count must be a nonnegative integer")
        size = min(self.seen, REPLAY_CAPACITY)
        slots = (self.sampling_rng.choice(size, min(count, size), replace=False)
                 if size and count else np.empty(0, dtype=np.int64))
        return (self.x[slots].copy(), self.y[slots].copy(),
                self.indices[slots].copy())

    def add(self, x, y):
        x = observation(x, y)
        slot = (self.seen if self.seen < REPLAY_CAPACITY
                else int(self.replacement_rng.integers(self.seen + 1)))
        if slot < REPLAY_CAPACITY:
            self.x[slot], self.y[slot], self.indices[slot] = x, int(y), self.seen
        self.seen += 1

    def state_dict(self):
        return {
            "x": torch.from_numpy(self.x.copy()),
            "y": torch.from_numpy(self.y.copy()),
            "indices": torch.from_numpy(self.indices.copy()),
            "seen": self.seen,
            "replacement_rng": copy.deepcopy(self.replacement_rng.bit_generator.state),
            "sampling_rng": copy.deepcopy(self.sampling_rng.bit_generator.state),
        }

    def load_state_dict(self, state):
        if type(state["seen"]) is not int or state["seen"] < 0:
            raise ValueError("Invalid reservoir observation count")
        arrays = {key: state[key].cpu().numpy().copy()
                  for key in ("x", "y", "indices")}
        for key, array in arrays.items():
            expected = getattr(self, key)
            if array.shape != expected.shape or array.dtype != expected.dtype:
                raise ValueError("Reservoir checkpoint shape or dtype mismatch")
        if not np.isfinite(arrays["x"]).all():
            raise ValueError("Nonfinite reservoir observation")
        used = min(state["seen"], REPLAY_CAPACITY)
        if (np.any(arrays["y"][:used] < 0)
                or np.any(arrays["y"][:used] >= CLASSES)
                or np.any(arrays["indices"][:used] < 0)
                or np.any(arrays["indices"][:used] >= state["seen"])
                or len(np.unique(arrays["indices"][:used])) != used):
            raise ValueError("Invalid reservoir labels or indices")
        self.x, self.y, self.indices = (arrays[k] for k in ("x", "y", "indices"))
        self.seen = state["seen"]
        self.replacement_rng.bit_generator.state = copy.deepcopy(state["replacement_rng"])
        self.sampling_rng.bit_generator.state = copy.deepcopy(state["sampling_rng"])