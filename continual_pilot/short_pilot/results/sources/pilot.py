"""CPU-only, prequential continual-learning pilot. No task IDs reach the learner."""
import argparse
import copy
import csv
import json
import platform
import time
from collections import deque
from pathlib import Path

import numpy as np
import torch
from torch import nn


class Generator:
    def __init__(self, seed=7, alpha=0.5, noise=0.05):
        self.alpha, self.noise = alpha, noise
        rng = np.random.default_rng(seed)
        self.w = np.linalg.qr(rng.normal(size=(32, 8)))[0]
        self.means = np.zeros((4, 8))
        self.means[:, :2] = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
        self.weights = (np.array([.4, .3, .2, .1]),
                        np.array([.1, .2, .3, .4]))
        self.teachers = []
        calibration = rng.normal(size=(20000, 2))
        for _ in range(3):
            a = rng.normal(size=(2, 16))
            b = rng.normal(size=(16, 4)) / 4
            raw = np.tanh(calibration @ a) @ b
            # Center each example across classes; normalize with one scalar.
            centered = raw - raw.mean(axis=1, keepdims=True)
            self.teachers.append((a, b, float(centered.std())))

    def component(self, z, index):
        a, b, scale = self.teachers[index]
        raw = np.tanh(z @ a) @ b
        return (raw - raw.mean(axis=1, keepdims=True)) / scale

    def labels(self, z, rule):
        common = self.component(z[:, :2], 0)
        specific = self.component(z[:, 2:4] if rule == 0 else z[:, 4:6],
                                  rule + 1)
        return (self.alpha * common + specific).argmax(axis=1)

    def sample(self, count, mixture, rule, rng):
        components = rng.choice(4, size=count, p=self.weights[mixture])
        z = rng.normal(size=(count, 8)) + self.means[components]
        clean = self.labels(z, rule)
        flip = rng.random(count) < self.noise
        offsets = rng.integers(1, 4, size=count)
        noisy = np.where(flip, (clean + offsets) % 4, clean)
        return (z @ self.w.T).astype(np.float32), noisy, clean, z

    def stream(self, length, seed, health=False):
        rng = np.random.default_rng(seed)
        schedule = [(0, 0)] if health else [(0, 0), (1, 0), (1, 1), (1, 0)]
        pieces = [self.sample(length, mixture, rule, rng)[:3]
                  for mixture, rule in schedule]
        return tuple(np.concatenate([piece[i] for piece in pieces])
                     for i in range(3))

    def diagnostics(self, seed, count=10000):
        rng = np.random.default_rng(seed)
        result = {}
        for mixture in range(2):
            _, noisy, clean, z = self.sample(count, mixture, 0, rng)
            second = self.labels(z, 1)
            result[f"M{mixture + 1}"] = {
                "disagreement": float(np.mean(clean != second)),
                "R1_class_fractions": (np.bincount(clean, minlength=4) / count).tolist(),
                "R2_class_fractions": (np.bincount(second, minlength=4) / count).tolist(),
                "observed_noise": float(np.mean(clean != noisy)),
            }
        return result


class Context:
    """Exactly the last window observed pairs; encode does not mutate state."""
    def __init__(self, window=64):
        self.window = window
        self.history = deque()
        self.sums = np.zeros((4, 32), dtype=np.float32)
        self.counts = np.zeros(4, dtype=np.int64)

    def encode(self, x):
        means = self.sums / np.maximum(self.counts[:, None], 1)
        frequencies = self.counts / max(len(self.history), 1)
        return np.concatenate((x, frequencies, means.ravel())).astype(np.float32)

    def observe(self, x, y):
        if len(self.history) == self.window:
            old_x, old_y = self.history.popleft()
            self.sums[old_y] -= old_x
            self.counts[old_y] -= 1
        self.history.append((x.copy(), int(y)))
        self.sums[y] += x
        self.counts[y] += 1

    def payload_bytes(self):
        return (self.sums.nbytes + self.counts.nbytes
                + self.window * (32 * 4 + 8))


class Reservoir:
    """Uniform reservoir over past encoded examples; task-agnostic."""
    def __init__(self, capacity, dimension, seed):
        self.capacity = capacity
        self.x = np.empty((capacity, dimension), dtype=np.float32)
        self.y = np.empty(capacity, dtype=np.int64)
        self.seen = 0
        # Keep sampling randomness independent of reservoir replacement.
        self.replace_rng = np.random.default_rng(seed)
        self.sample_rng = np.random.default_rng(seed + 1)

    def sample(self, count):
        size = min(self.seen, self.capacity)
        if size == 0 or count == 0:
            return self.x[:0], self.y[:0]
        ids = self.sample_rng.choice(size, size=min(count, size), replace=False)
        return self.x[ids], self.y[ids]

    def add(self, x, y):
        index = (self.seen if self.seen < self.capacity
                 else int(self.replace_rng.integers(self.seen + 1)))
        if index < self.capacity:
            self.x[index], self.y[index] = x, y
        self.seen += 1


def make_model(hidden):
    return nn.Sequential(nn.Linear(164, hidden), nn.ReLU(), nn.Linear(hidden, 4))


def tensor_bytes(values):
    return sum(value.numel() * value.element_size()
               for value in values if isinstance(value, torch.Tensor))


def run(initial, stream, args, replay=False):
    model = copy.deepcopy(initial)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    context = Context(args.context_window)
    buffer = Reservoir(args.capacity if replay else 0, 164, args.seed + 300)
    x, y, clean = stream
    predictions = np.empty(len(y), dtype=np.int64)
    examples_trained = 0
    maximum_batch = 0
    start = time.perf_counter()
    for t in range(len(y)):
        # Neither y[t] nor a phase ID is available when this feature is built.
        encoded = context.encode(x[t])
        current = torch.from_numpy(encoded).unsqueeze(0)
        model.eval()
        with torch.no_grad():
            predictions[t] = int(model(current).argmax(dim=1).item())
        old_x, old_y = buffer.sample(args.replay_batch if replay else 0)
        train_x = torch.from_numpy(np.concatenate((encoded[None], old_x)))
        train_y = torch.from_numpy(np.concatenate((y[t:t + 1], old_y)))
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(model(train_x), train_y)
        loss.backward()
        optimizer.step()
        examples_trained += len(train_y)
        maximum_batch = max(maximum_batch, len(train_y))
        # Add current example only after sampling and the learning update.
        if replay:
            buffer.add(encoded, y[t])
        context.observe(x[t], y[t])
    elapsed = time.perf_counter() - start
    parameters = sum(p.numel() for p in model.parameters())
    parameter_bytes = tensor_bytes(model.parameters())
    gradient_bytes = tensor_bytes(p.grad for p in model.parameters())
    optimizer_bytes = sum(tensor_bytes(state.values())
                          for state in optimizer.state.values())
    buffer_bytes = buffer.x.nbytes + buffer.y.nbytes
    persistent = parameter_bytes + optimizer_bytes + buffer_bytes + context.payload_bytes()
    # Approximation: dense linear forward MACs only, backward ~= 2 forwards.
    linear_macs = 164 * args.hidden + args.hidden * 4
    estimated_flops = 2 * linear_macs * (len(y) + 3 * examples_trained)
    return {
        "predictions": predictions,
        "seconds": elapsed,
        "parameters": parameters,
        "parameter_bytes": parameter_bytes,
        "gradient_bytes": gradient_bytes,
        "optimizer_tensor_bytes": optimizer_bytes,
        "replay_allocated_bytes": buffer_bytes,
        "context_payload_capacity_bytes": context.payload_bytes(),
        "persistent_tensor_payload_bytes": persistent,
        "payload_with_gradients_bytes": persistent + gradient_bytes,
        "training_examples_including_replay": examples_trained,
        "optimizer_steps": len(y),
        "maximum_training_batch": maximum_batch,
        "approx_dense_linear_flops": estimated_flops,
    }


def evaluate(result, stream, phase_length, block_size):
    _, y, clean = stream
    prediction = result.pop("predictions")
    error = (prediction != y).astype(np.int64)
    oracle_error = (clean != y).astype(np.int64)
    regret = error - oracle_error
    result["phases"] = []
    rows = []
    for start in range(0, len(y), phase_length):
        stop = min(start + phase_length, len(y))
        phase_regret = regret[start:stop]
        result["phases"].append({
            "phase": start // phase_length + 1,
            "accuracy": float(np.mean(prediction[start:stop] == y[start:stop])),
            "clean_rule_accuracy": float(np.mean(prediction[start:stop] == clean[start:stop])),
            "oracle_accuracy": float(np.mean(clean[start:stop] == y[start:stop])),
            "first_window_size": min(1000, stop - start),
            "first_window_regret": int(phase_regret[:1000].sum()),
            "total_regret": int(phase_regret.sum()),
            "last_1000_accuracy": float(np.mean(error[max(start, stop - 1000):stop] == 0)),
        })
        cumulative = 0
        for left in range(start, stop, block_size):
            right = min(left + block_size, stop)
            cumulative += int(regret[left:right].sum())
            rows.append({
                "phase": start // phase_length + 1,
                "step_end": right,
                "phase_step_end": right - start,
                "count": right - left,
                "accuracy": float(np.mean(error[left:right] == 0)),
                "oracle_accuracy": float(np.mean(oracle_error[left:right] == 0)),
                "regret": int(regret[left:right].sum()),
                "cumulative_phase_regret": cumulative,
            })
    return rows


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--noise", type=float, default=0.05)
    parser.add_argument("--phase-length", type=int, default=5000)
    parser.add_argument("--health-length", type=int, default=10000)
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--capacity", type=int, default=512)
    parser.add_argument("--replay-batch", type=int, default=8)
    parser.add_argument("--context-window", type=int, default=64)
    parser.add_argument("--block-size", type=int, default=200)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    for name in ("phase_length", "health_length", "hidden", "capacity",
                 "replay_batch", "context_window", "block_size", "threads"):
        if getattr(args, name) < 1:
            parser.error(f"{name} must be positive")
    if not (0 <= args.noise < 0.75) or args.alpha < 0 or args.lr <= 0:
        parser.error("Require 0 <= noise < .75, alpha >= 0 and lr > 0")
    return args


def main():
    args = parse_args()
    torch.set_num_threads(args.threads)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(args.seed)
    generator = Generator(args.seed, args.alpha, args.noise)
    initial = make_model(args.hidden)
    report = {
        "config": {key: str(value) if isinstance(value, Path) else value
                   for key, value in vars(args).items()},
        "environment": {"python": platform.python_version(), "torch": torch.__version__,
                        "numpy": np.__version__, "device": "cpu"},
        "generator": generator.diagnostics(args.seed + 900),
        "limitations": [
            "Single seed, exploratory pilot, not a significance test.",
            "Same model and stream; replay uses extra memory and training compute.",
            "Replay retains historical context, not reconstructed current context.",
            "Memory is explicit payload accounting, NOT measured process peak RSS.",
            "Python overhead, activations, temporary batches and evaluator data excluded.",
            "FLOPs approximate linear layers only; timings include online maintenance.",
            "No routing, renewal, changepoint detector or plasticity probe implemented.",
        ],
        "runs": {},
    }
    all_rows = []
    for experiment, length in (("health", args.health_length), ("stream", args.phase_length)):
        stream = generator.stream(length, args.seed + (100 if experiment == "health" else 200),
                                  health=experiment == "health")
        for method, replay in (("A", False), ("replay", True)):
            name = f"{experiment}_{method}"
            print(f"Running {name}: {len(stream[1])} examples", flush=True)
            result = run(initial, stream, args, replay)
            rows = evaluate(result, stream, length, args.block_size)
            all_rows.extend({"run": name, **row} for row in rows)
            report["runs"][name] = result
            print(f"{name}: {result['seconds']:.2f}s; phases={result['phases']}", flush=True)
    a = report["runs"]["stream_A"]["phases"][3]["first_window_regret"]
    b = report["runs"]["stream_replay"]["phases"][3]["first_window_regret"]
    report["phase4_replay_minus_A_regret"] = b - a
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (args.output / "curves.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Phase 4 replay - A regret: {b - a}; negative favors replay.")
    print(f"Results: {args.output.resolve()}")


if __name__ == "__main__":
    main()