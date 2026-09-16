"""Loss-supervised router; no rule IDs, clean labels or experiment on import."""
import copy

import numpy as np
import torch
from torch import nn

from .config import CONTEXT_DIM, EXPERTS
from .expert import adam


class Router:
    """Linear router trained once on each completed group's stored summary.

    The caller computes both experts' noisy losses BEFORE either expert updates.
    Forced exploration is a separate global schedule, not a learned target.
    """

    def __init__(self):
        # Linear construction consumes randomness before zeroing. Isolate it.
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(0)
            self.model = nn.Linear(CONTEXT_DIM, EXPERTS)
        with torch.no_grad():
            self.model.weight.zero_()
            self.model.bias.zero_()
        self.optimizer = adam(self.model.parameters())
        self.updates = 0

    @staticmethod
    def _summary(summary):
        array = np.array(summary, dtype=np.float32, copy=True)
        if array.shape != (CONTEXT_DIM,) or not np.isfinite(array).all():
            raise ValueError("Expected one finite 132-dimensional context summary")
        return torch.from_numpy(array).unsqueeze(0)

    def scores(self, summary):
        with torch.no_grad():
            scores = self.model(self._summary(summary))[0]
        if not torch.isfinite(scores).all():
            raise ValueError("Nonfinite router prediction")
        return scores.numpy().copy()

    def greedy(self, summary):
        """argmax resolves exact score ties to the lower expert index."""
        return int(self.scores(summary).argmax())

    def update(self, group_start_summary, preupdate_mean_noisy_losses):
        """Target the lower-loss expert, resolving exact ties to expert zero."""
        losses = np.asarray(preupdate_mean_noisy_losses, dtype=np.float64)
        if losses.shape != (EXPERTS,) or not np.isfinite(losses).all():
            raise ValueError("Expected two finite pre-update mean noisy losses")
        if np.any(losses < 0):
            raise ValueError("Cross-entropy losses cannot be negative")
        target = int(losses.argmin())
        inputs = self._summary(group_start_summary)
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(
            self.model(inputs), torch.tensor([target], dtype=torch.int64))
        if not torch.isfinite(loss):
            raise ValueError("Nonfinite router training loss")
        loss.backward()
        if any(p.grad is None or not torch.isfinite(p.grad).all()
               for p in self.model.parameters()):
            raise ValueError("Missing or nonfinite router gradient")
        self.optimizer.step()
        if any(not torch.isfinite(p).all() for p in self.model.parameters()):
            raise ValueError("Nonfinite updated router weights")
        self.updates += 1
        return {
            "target_expert": target,
            "preupdate_mean_noisy_losses": losses.tolist(),
            "router_loss": float(loss.detach()),
        }

    def state_dict(self):
        return copy.deepcopy({
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "gradients": [None if p.grad is None else p.grad.detach().clone()
                          for p in self.model.parameters()],
            "training": self.model.training,
            "updates": self.updates,
        })

    @classmethod
    def from_state_dict(cls, state):
        router = cls()
        router.model.load_state_dict(state["model"], strict=True)
        router.optimizer.load_state_dict(copy.deepcopy(state["optimizer"]))
        parameters = list(router.model.parameters())
        if len(state["gradients"]) != len(parameters):
            raise ValueError("Router checkpoint gradient structure mismatch")
        for parameter, gradient in zip(parameters, state["gradients"]):
            if gradient is not None:
                if (gradient.shape != parameter.shape
                        or not torch.isfinite(gradient).all()):
                    raise ValueError("Invalid router checkpoint gradient")
            parameter.grad = None if gradient is None else gradient.detach().clone()
        if type(state["training"]) is not bool:
            raise ValueError("Invalid router checkpoint training mode")
        router.model.train(state["training"])
        if type(state["updates"]) is not int or state["updates"] < 0:
            raise ValueError("Invalid router checkpoint update count")
        router.updates = state["updates"]
        if any(not torch.isfinite(p).all() for p in router.model.parameters()):
            raise ValueError("Nonfinite router checkpoint weights")
        return router