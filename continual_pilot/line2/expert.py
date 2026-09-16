"""CPU expert with complete local training state; no experiment on import."""
import copy

import numpy as np
import torch
from torch import nn

from .config import (
    ADAM_BETAS, ADAM_EPSILON, CLASSES, CONTEXT_DIM, HIDDEN_DIM,
    INPUT_DIM, LEARNING_RATE,
)
from .cpr import PartialReset


def adam(parameters):
    return torch.optim.Adam(
        parameters, lr=LEARNING_RATE, betas=ADAM_BETAS,
        eps=ADAM_EPSILON, weight_decay=0.0)


class Expert:
    """One independently clocked expert; callers supply only noisy targets."""

    def __init__(self, *, model_seed, cpr_seed=None, context=False):
        if context and cpr_seed is not None:
            raise ValueError("The context diagnostic has no CPR condition")
        self.spec = {
            "model_seed": model_seed, "cpr_seed": cpr_seed, "context": bool(context)
        }
        dimension = INPUT_DIM + (CONTEXT_DIM if context else 0)
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(model_seed)
            self.model = nn.Sequential(
                nn.Linear(dimension, HIDDEN_DIM), nn.ReLU(),
                nn.Linear(HIDDEN_DIM, CLASSES))
        self.optimizer = adam(self.model.parameters())
        self.cpr = (None if cpr_seed is None
                    else PartialReset(self.model, seed=cpr_seed))
        self.updates = 0
        self.training_examples = 0
        self.utility_gradient_evaluations = 0

    def _inputs(self, x):
        array = np.array(x, dtype=np.float32, copy=True)
        if (array.ndim != 2 or array.shape[1] != self.model[0].in_features
                or not np.isfinite(array).all()):
            raise ValueError("Invalid expert input matrix")
        return torch.from_numpy(array)

    def scores(self, x):
        """No gradients, mode changes, clocks, context or RNG consumption."""
        with torch.no_grad():
            scores = self.model(self._inputs(x))
        if not torch.isfinite(scores).all():
            raise ValueError("Nonfinite expert prediction")
        return scores.numpy().copy()

    def update(self, x, noisy):
        inputs = self._inputs(x)
        labels = np.asarray(noisy)
        if (labels.shape != (len(inputs),) or len(labels) == 0
                or labels.dtype.kind not in "iu"
                or np.any(labels < 0) or np.any(labels >= CLASSES)):
            raise ValueError("Expected matching nonempty noisy integer labels")
        targets = torch.from_numpy(labels.astype(np.int64, copy=True))
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        losses = nn.functional.cross_entropy(
            self.model(inputs), targets, reduction="none")
        if not torch.isfinite(losses).all():
            raise ValueError("Nonfinite expert training loss")
        raw_utility = None
        if self.cpr is not None:
            raw_utility = self.cpr.observe(self.model, losses)
        losses.mean().backward()
        if any(p.grad is None or not torch.isfinite(p.grad).all()
               for p in self.model.parameters()):
            raise ValueError("Missing or nonfinite expert gradient")
        self.optimizer.step()
        event = (None if self.cpr is None
                 else self.cpr.after_optimizer_step(self.model))
        if any(not torch.isfinite(p).all() for p in self.model.parameters()):
            raise ValueError("Nonfinite updated expert weights")
        self.updates += 1
        self.training_examples += len(labels)
        if self.cpr is not None:
            self.utility_gradient_evaluations += len(labels)
            if self.cpr.local_updates != self.updates:
                raise AssertionError("CPR and expert local clocks disagree")
        return {
            "mean_noisy_loss": float(losses.detach().mean()),
            "training_examples": len(labels),
            "raw_utility": None if raw_utility is None else raw_utility.tolist(),
            "cpr_event": event,
        }

    def state_dict(self):
        return copy.deepcopy({
            "spec": self.spec,
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "gradients": [None if p.grad is None else p.grad.detach().clone()
                          for p in self.model.parameters()],
            "module_training": [module.training for module in self.model.modules()],
            "updates": self.updates,
            "training_examples": self.training_examples,
            "utility_gradient_evaluations": self.utility_gradient_evaluations,
            "cpr": None if self.cpr is None else self.cpr.state_dict(),
        })

    @classmethod
    def from_state_dict(cls, state):
        expert = cls(**state["spec"])
        expert.model.load_state_dict(state["model"], strict=True)
        expert.optimizer.load_state_dict(copy.deepcopy(state["optimizer"]))
        parameters = list(expert.model.parameters())
        modules = list(expert.model.modules())
        if (len(state["gradients"]) != len(parameters)
                or len(state["module_training"]) != len(modules)):
            raise ValueError("Expert checkpoint structure mismatch")
        for parameter, gradient in zip(parameters, state["gradients"]):
            parameter.grad = None if gradient is None else gradient.detach().clone()
        for module, training in zip(modules, state["module_training"]):
            module.training = bool(training)
        for key in ("updates", "training_examples", "utility_gradient_evaluations"):
            if type(state[key]) is not int or state[key] < 0:
                raise ValueError("Invalid expert checkpoint counter")
            setattr(expert, key, state[key])
        if (expert.cpr is None) != (state["cpr"] is None):
            raise ValueError("CPR checkpoint condition mismatch")
        if expert.cpr is not None:
            expert.cpr.load_state_dict(state["cpr"])
            if expert.cpr.local_updates != expert.updates:
                raise ValueError("Checkpoint expert and CPR clocks disagree")
            if expert.cpr.pending_observation:
                raise ValueError("Cannot resume an incomplete autograd update")
        return expert