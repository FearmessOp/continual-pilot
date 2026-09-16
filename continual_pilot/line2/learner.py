"""Causal Line 2 learner assembly; no experiment or generator on import."""
import copy

import numpy as np
import torch

from .config import MINIBATCH, REPLAY_PER_NEW
from .expert import Expert
from .memory import History, RecentKNN, ReplayMemory, observation
from .router import Router
from .schedule import exploration_expert, update_due


BASE_METHODS = ("A", "B", "C", "D", "replay", "knn", "A+context")
BRANCH_RATES = {"frozen-F2": 0, "sparse25": 25, "sparse50": 50, "sparse75": 75}


class Learner:
    """Predict/observe handshake with group-boundary portable checkpoints.

    No phase, regime, clean target or evaluator metadata enters this interface.
    Seeds are explicit manifest values. CPR expert-zero streams must be paired
    between C and D by the caller, as must the model initialization streams.
    """

    def __init__(self, method, *, seeds):
        if method not in BASE_METHODS:
            raise ValueError("Sparse/frozen conditions must branch from A")
        self.method = method
        self.seeds = copy.deepcopy(seeds)
        self.rate_percent = 100
        routed = method in ("B", "D")
        renewal = method in ("C", "D")
        self.experts = [
            Expert(model_seed=seeds[f"model{i}"],
                   cpr_seed=seeds[f"cpr{i}"] if renewal else None,
                   context=method == "A+context")
            for i in range(0 if method == "knn" else (2 if routed else 1))
        ]
        self.router = Router() if routed else None
        self.history = History()
        self.knn = RecentKNN() if method == "knn" else None
        self.replay = (ReplayMemory(
            replacement_seed=seeds["reservoir-replacement"],
            sampling_seed=seeds["reservoir-sampling"])
            if method == "replay" else None)
        self.examples_seen = 0
        self.groups_completed = 0
        self.selected_groups = [0] * len(self.experts)
        self.forced_groups = [0] * len(self.experts)
        self.greedy_groups = [0] * len(self.experts)
        self.replay_examples = 0
        self.maximum_training_batch = 0
        self.awaiting = None
        self.group = None

    def _begin_group(self):
        number = self.groups_completed + 1
        summary = self.history.summary()
        forced = exploration_expert(number) if self.router is not None else None
        greedy = self.router.greedy(summary) if self.router is not None else 0
        selected = forced if forced is not None else greedy
        self.group = {
            "number": number, "summary": summary, "forced": forced,
            "greedy": greedy, "selected": selected, "count": 0,
            "x": [], "y": [], "losses": [], "replay_indices": [],
        }

    def predict(self, x):
        """Issue exactly one prediction before accepting its noisy label."""
        if self.awaiting is not None:
            raise RuntimeError("Observe the previous prediction before predicting again")
        x = observation(x)
        if self.group is None:
            self._begin_group()
        features = self.history.encode(x) if self.method == "A+context" else x
        scores = [expert.scores(features[None])[0] for expert in self.experts]
        prediction = (self.knn.predict_one(x) if self.knn is not None
                      else int(scores[self.group["selected"]].argmax()))
        self.awaiting = {"x": x, "features": features.copy(),
                         "scores": scores, "prediction": prediction}
        return prediction

    def observe(self, noisy):
        """Consume the issued prediction's noisy label; update only at group end."""
        if self.awaiting is None:
            raise RuntimeError("A prediction must precede each observed label")
        pending = self.awaiting
        observation(pending["x"], noisy)
        noisy = int(noisy)
        group = self.group
        if self.router is not None:
            logits = torch.from_numpy(np.stack(pending["scores"]))
            targets = torch.full((2,), noisy, dtype=torch.int64)
            losses = torch.nn.functional.cross_entropy(
                logits, targets, reduction="none").numpy()
            if not np.isfinite(losses).all():
                raise ValueError("Nonfinite pre-update expert loss")
            group["losses"].append(losses)
        group["x"].append(pending["features"].copy())
        group["y"].append(noisy)
        sampled_indices = np.empty(0, dtype=np.int64)
        if self.replay is not None:
            old_x, old_y, sampled_indices = self.replay.sample(REPLAY_PER_NEW)
            group["x"].extend(old_x)
            group["y"].extend(int(y) for y in old_y)
            group["replay_indices"].append(sampled_indices.tolist())
            self.replay_examples += len(old_y)
        group["count"] += 1
        result = None
        if group["count"] == MINIBATCH:
            selected = group["selected"]
            router_result = None
            if self.router is not None:
                mean_losses = np.stack(group["losses"]).mean(axis=0)
                router_result = self.router.update(group["summary"], mean_losses)
            due = bool(self.experts) and update_due(
                group["number"], rate_percent=self.rate_percent)
            update_result = None
            if due:
                update_result = self.experts[selected].update(
                    np.stack(group["x"]), np.asarray(group["y"], dtype=np.int64))
                self.maximum_training_batch = max(
                    self.maximum_training_batch, len(group["y"]))
            if self.experts:
                self.selected_groups[selected] += 1
                if group["forced"] is not None:
                    self.forced_groups[selected] += 1
                else:
                    self.greedy_groups[selected] += 1
            self.groups_completed += 1
            result = {
                "global_group": group["number"],
                "selected_expert": selected if self.experts else None,
                "forced_expert": group["forced"],
                "greedy_expert": group["greedy"] if self.router is not None else None,
                "group_start_summary": group["summary"].copy(),
                "expert_updated": due,
                "router": router_result,
                "expert_update": update_result,
                "replay_indices": copy.deepcopy(group["replay_indices"]),
            }
        # Latest observation enters memory only after its prediction and update.
        if self.replay is not None:
            self.replay.add(pending["x"], noisy)
        if self.knn is not None:
            self.knn.observe(pending["x"], noisy)
        # Frozen-F2 preserves its phase-2 context too, though A does not use it.
        if self.method != "frozen-F2":
            self.history.observe(pending["x"], noisy)
        self.examples_seen += 1
        self.awaiting = None
        if result is not None:
            self.group = None
        return {
            "index": self.examples_seen - 1,
            "prediction": pending["prediction"],
            "sampled_replay_indices": sampled_indices.copy(),
            "completed_group": result,
        }

    def _require_boundary(self):
        if self.awaiting is not None or self.group is not None:
            raise RuntimeError("This operation requires a completed group boundary")
        if self.examples_seen != self.groups_completed * MINIBATCH:
            raise AssertionError("Global example and group clocks disagree")

    def frozen_predictions(self, x):
        """Greedy frozen policy; rowwise arithmetic is independent of test order."""
        self._require_boundary()
        inputs = np.asarray(x, dtype=np.float32)
        if (inputs.ndim != 2 or inputs.shape[1] != 32
                or not np.isfinite(inputs).all()):
            raise ValueError("Expected finite evaluation inputs")
        selected = self.router.greedy(self.history.summary()) if self.router else 0
        predictions = []
        for row in inputs:
            if self.knn is not None:
                prediction = self.knn.predict_one(row)
            else:
                features = self.history.encode(row) if self.method == "A+context" else row
                prediction = int(self.experts[selected].scores(features[None])[0].argmax())
            predictions.append(prediction)
        return np.asarray(predictions, dtype=np.int64)

    def checkpoint(self):
        """Save all mutable training state at supported completed-group boundaries."""
        self._require_boundary()
        return copy.deepcopy({
            "schema": "line2-learner-v1",
            "method": self.method, "seeds": self.seeds, "rate_percent": self.rate_percent,
            "experts": [expert.state_dict() for expert in self.experts],
            "router": None if self.router is None else self.router.state_dict(),
            "history": self.history.state_dict(),
            "knn": None if self.knn is None else self.knn.state_dict(),
            "replay": None if self.replay is None else self.replay.state_dict(),
            "examples_seen": self.examples_seen, "groups_completed": self.groups_completed,
            "selected_groups": self.selected_groups, "forced_groups": self.forced_groups,
            "greedy_groups": self.greedy_groups, "replay_examples": self.replay_examples,
            "maximum_training_batch": self.maximum_training_batch,
        })

    @classmethod
    def from_checkpoint(cls, state):
        if state["schema"] != "line2-learner-v1":
            raise ValueError("Unknown learner checkpoint schema")
        method = state["method"]
        base = "A" if method in BRANCH_RATES else method
        learner = cls(base, seeds=state["seeds"])
        expected_rate = BRANCH_RATES.get(method, 100)
        if state["rate_percent"] != expected_rate:
            raise ValueError("Checkpoint update policy differs from condition")
        learner.method, learner.rate_percent = method, expected_rate
        if len(state["experts"]) != len(learner.experts):
            raise ValueError("Checkpoint expert count mismatch")
        learner.experts = [Expert.from_state_dict(s) for s in state["experts"]]
        if (state["router"] is None) != (learner.router is None):
            raise ValueError("Checkpoint router condition mismatch")
        if learner.router is not None:
            learner.router = Router.from_state_dict(state["router"])
        learner.history.load_state_dict(state["history"])
        for name in ("knn", "replay"):
            memory = getattr(learner, name)
            if (state[name] is None) != (memory is None):
                raise ValueError("Checkpoint memory condition mismatch")
            if memory is not None:
                memory.load_state_dict(state[name])
        for name in ("examples_seen", "groups_completed", "replay_examples",
                     "maximum_training_batch"):
            if type(state[name]) is not int or state[name] < 0:
                raise ValueError("Invalid checkpoint counter")
            setattr(learner, name, state[name])
        for name in ("selected_groups", "forced_groups", "greedy_groups"):
            values = state[name]
            if (len(values) != len(learner.experts)
                    or any(type(v) is not int or v < 0 for v in values)):
                raise ValueError("Invalid checkpoint expert counters")
            setattr(learner, name, list(values))
        learner._require_boundary()
        return learner

    def fork(self):
        return self.from_checkpoint(self.checkpoint())

    def branch_from_a(self, method):
        """Explicit experimental branching; never infer a boundary from labels."""
        self._require_boundary()
        if self.method != "A" or method not in BRANCH_RATES:
            raise ValueError("Only A can create a sparse/frozen reference branch")
        child = self.fork()
        child.method = method
        child.rate_percent = BRANCH_RATES[method]
        return child