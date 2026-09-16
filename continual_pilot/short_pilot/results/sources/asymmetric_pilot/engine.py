"""Asymmetric exploratory pilot mechanics; no experiment runs on import."""
import copy
import hashlib
import json

import numpy as np
import torch
from torch import nn

import diagnose
from pilot import Reservoir


CONFIG = {
    "generator_seed": 1000,
    "alpha": 0.5,
    "noise": 0.05,
    "calibration_count": 20000,
    "hidden": 64,
    "model_seed": 7,
    "lr": 0.001,
    "minibatch": 16,
    "capacity": 512,
    "replay_per_new_example": 8,
    "stream_seeds": [230001, 230002, 230003],
    "phase1_count": 40000,
    "phase2_count": 10000,
    "phase3_candidates": [2000, 4000],
    "phase4_count": 4000,
    "evaluation_seed": 239001,
    "evaluation_count": 20000,
    "window_updates": 30,
    "minimum_phase2_accuracy": 0.80,
    "damage_band": [0.20, 0.40],
}
LABEL = "Exploration-derived phase-length pilot; learnability gate NOT passed."


def tree_digest(value):
    """Canonical typed digest of nested numerical state, independent of pickle."""
    digest = hashlib.sha256()

    def visit(item):
        if isinstance(item, torch.Tensor):
            visit(item.detach().cpu().numpy())
        elif isinstance(item, np.ndarray):
            digest.update(b"array")
            visit(item.dtype.str)
            visit(list(item.shape))
            digest.update(np.ascontiguousarray(item).tobytes())
        elif isinstance(item, dict):
            digest.update(b"dict")
            for key in sorted(item, key=lambda k: (type(k).__name__, str(k))):
                visit(key)
                visit(item[key])
        elif isinstance(item, (tuple, list)):
            digest.update(b"sequence")
            visit(len(item))
            for child in item:
                visit(child)
        elif isinstance(item, np.generic):
            visit(item.item())
        else:
            encoded = json.dumps(item, allow_nan=False).encode("utf-8")
            digest.update(type(item).__name__.encode("ascii"))
            digest.update(str(len(encoded)).encode("ascii") + b":" + encoded)

    visit(value)
    return digest.hexdigest()


def sample_phase(generator, count, mixture, rule, seed):
    x, noisy, clean, z = generator.sample(
        count, mixture, rule, np.random.default_rng(seed))
    return {"x": x, "noisy": noisy, "clean": clean, "z": z,
            "index": np.arange(count, dtype=np.int64)}


def prefix(data, count):
    if not 0 < count <= len(data["noisy"]):
        raise ValueError("Invalid prefix length")
    return {key: array[:count] for key, array in data.items()}


def make_streams(generator, seed, config):
    """Phase 3 is drawn ONCE at maximum length; candidates use its prefixes."""
    lengths = [config["phase1_count"], config["phase2_count"],
               max(config["phase3_candidates"]), config["phase4_count"]]
    schedule = [(0, 0), (1, 0), (1, 1), (1, 0)]
    return {
        str(phase): sample_phase(generator, length, mixture, rule,
                                 seed + (phase - 1) * 1000)
        for phase, (length, (mixture, rule)) in enumerate(
            zip(lengths, schedule), 1)
    }


def make_evaluation(generator, config):
    data = sample_phase(generator, config["evaluation_count"], 1, 0,
                        config["evaluation_seed"])
    data["r1"] = data["clean"].copy()
    data["r2"] = generator.labels(data["z"], 1)
    return data


class Learner:
    """One model/Adam/reservoir bundle; clean labels never enter training."""

    def __init__(self, initial, *, replay, reservoir_seed, config):
        self.config = copy.deepcopy(config)
        self.replay = bool(replay)
        self.model = copy.deepcopy(initial)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=config["lr"])
        self.buffer = Reservoir(config["capacity"] if replay else 0, 32,
                                reservoir_seed)
        # Avoid uninitialized unused storage in checkpoints.
        self.buffer.x.fill(0)
        self.buffer.y.fill(0)
        self.steps = 0
        self.examples_seen = 0

    def checkpoint(self):
        """Portable CPU state at a completed group boundary."""
        return copy.deepcopy({
            "config": self.config,
            "replay": self.replay,
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "steps": self.steps,
            "examples_seen": self.examples_seen,
            "buffer": {
                "capacity": self.buffer.capacity,
                "seen": self.buffer.seen,
                "x": torch.from_numpy(self.buffer.x.copy()),
                "y": torch.from_numpy(self.buffer.y.copy()),
                "replace_rng": self.buffer.replace_rng.bit_generator.state,
                "sample_rng": self.buffer.sample_rng.bit_generator.state,
            },
        })

    @classmethod
    def from_checkpoint(cls, state):
        initial = diagnose.make_model(state["config"]["hidden"], False,
                                      seed=state["config"]["model_seed"])
        learner = cls(initial, replay=state["replay"], reservoir_seed=0,
                      config=state["config"])
        learner.model.load_state_dict(state["model"])
        learner.optimizer.load_state_dict(copy.deepcopy(state["optimizer"]))
        learner.steps = state["steps"]
        learner.examples_seen = state["examples_seen"]
        b = state["buffer"]
        learner.buffer.x[:] = b["x"].cpu().numpy()
        learner.buffer.y[:] = b["y"].cpu().numpy()
        learner.buffer.seen = b["seen"]
        learner.buffer.replace_rng.bit_generator.state = copy.deepcopy(b["replace_rng"])
        learner.buffer.sample_rng.bit_generator.state = copy.deepcopy(b["sample_rng"])
        return learner

    def fork(self):
        # Deepcopy the bundle in one operation: optimizer parameters still refer
        # to the copied model, not to the source model.
        child = copy.deepcopy(self)
        if tree_digest(child.checkpoint()) != tree_digest(self.checkpoint()):
            raise AssertionError("Branch state mismatch")
        return child

    def train_phase(self, x, noisy):
        """Predict before each label; update after 16 NEW samples, plus replay."""
        if len(x) != len(noisy) or len(noisy) == 0:
            raise ValueError("Nonempty matching inputs and labels required")
        batch = self.config["minibatch"]
        predictions = np.empty(len(noisy), dtype=np.int64)
        pending_x, pending_y = [], []
        update_positions = []
        replay_examples = 0
        maximum_batch = 0
        for t in range(len(noisy)):
            self.model.eval()
            with torch.no_grad():
                predictions[t] = int(self.model(
                    torch.from_numpy(x[t]).unsqueeze(0)).argmax(dim=1).item())
            old_x, old_y = self.buffer.sample(
                self.config["replay_per_new_example"] if self.replay else 0)
            pending_x.append(x[t].copy())
            pending_y.append(int(noisy[t]))
            pending_x.extend(old_x)
            pending_y.extend(int(y) for y in old_y)
            replay_examples += len(old_y)
            if (t + 1) % batch == 0 or t + 1 == len(noisy):
                self.model.train()
                self.optimizer.zero_grad(set_to_none=True)
                loss = nn.functional.cross_entropy(
                    self.model(torch.from_numpy(np.stack(pending_x))),
                    torch.tensor(pending_y, dtype=torch.int64))
                loss.backward()
                self.optimizer.step()
                self.steps += 1
                update_positions.append(t + 1)
                maximum_batch = max(maximum_batch, len(pending_y))
                pending_x.clear()
                pending_y.clear()
            if self.replay:
                self.buffer.add(x[t], noisy[t])
            self.examples_seen += 1
        return {
            "predictions": predictions,
            "update_positions": np.asarray(update_positions, dtype=np.int64),
            "replay_examples": replay_examples,
            "maximum_batch": maximum_batch,
        }


def predict(model, x):
    """Frozen, batched evaluation; restore mode and check weights for mutation."""
    before = diagnose.state_digest(model)
    training = model.training
    try:
        model.eval()
        with torch.no_grad():
            predictions = model(torch.from_numpy(x)).argmax(dim=1).numpy()
    finally:
        model.train(training)
    if before != diagnose.state_digest(model):
        raise AssertionError("Frozen prediction changed weights")
    return predictions


def frozen_report(learner, evaluation):
    before = tree_digest(learner.checkpoint())
    predictions = predict(learner.model, evaluation["x"])
    if before != tree_digest(learner.checkpoint()):
        raise AssertionError("Evaluation changed learner state")
    return {
        "r1_accuracy": float(np.mean(predictions == evaluation["r1"])),
        "r2_accuracy": float(np.mean(predictions == evaluation["r2"])),
    }, predictions


def phase_metrics(result, data):
    pred, noisy, clean = result["predictions"], data["noisy"], data["clean"]
    if not (pred.shape == noisy.shape == clean.shape):
        raise ValueError("Prediction and target shapes differ")
    regret = (pred != noisy).astype(np.int64) - (clean != noisy).astype(np.int64)
    return {
        "count": len(clean),
        "optimizer_steps": len(result["update_positions"]),
        "clean_accuracy": float(np.mean(pred == clean)),
        "noisy_accuracy": float(np.mean(pred == noisy)),
        "oracle_regret": int(regret.sum()),
        "oracle_regret_per_example": float(regret.mean()),
        "replay_examples": int(result["replay_examples"]),
        "training_examples_including_replay": len(clean) + result["replay_examples"],
        "maximum_batch": int(result["maximum_batch"]),
    }


def window_metrics(online, reference, clean, update_positions, count):
    if count <= 0 or min(len(online), len(reference), len(clean)) < count:
        raise ValueError("Insufficient transition window")
    online_errors = int(np.sum(online[:count] != clean[:count]))
    reference_errors = int(np.sum(reference[:count] != clean[:count]))
    difference = online_errors - reference_errors
    return {
        "count": count,
        "updates": int(np.sum(update_positions <= count)),
        "online_clean_errors": online_errors,
        "phase2_reference_clean_errors": reference_errors,
        "extra_errors": difference,
        "extra_errors_per_example": difference / count,
    }


def select_candidate(rows, config):
    """Use A only. No widening or replacement if no candidate passes all seeds."""
    expected = set(config["stream_seeds"])
    a_rows = [row for row in rows if row["method"] == "A"]
    eligible = []
    for candidate in sorted(config["phase3_candidates"]):
        group = [row for row in a_rows if row["phase3_count"] == candidate]
        if len(group) != len(expected) or {r["seed"] for r in group} != expected:
            raise ValueError("Missing or duplicated A candidate rows")
        if all(r["frozen"]["2"]["r1_accuracy"] >= config["minimum_phase2_accuracy"]
               and config["damage_band"][0] <= r["damage"] <= config["damage_band"][1]
               for r in group):
            eligible.append(candidate)
    return {"eligible_candidates": eligible,
            "selected_phase3_count": min(eligible) if eligible else None,
            "scope": "v0.3 pilot only; no automatic transfer to filtered v0.4"}