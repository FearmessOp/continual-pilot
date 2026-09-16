"""Revision-1 CPR-style adaptation for the single hidden-layer expert.

Call observe() on the noisy minibatch losses BEFORE the optimizer update,
then after_optimizer_step() AFTER the update. Utility calculation does not
populate or change parameter .grad fields. No experiment runs on import.
"""
import copy

import torch

from .config import (
    CPR_EMA_DECAY, CPR_EPSILON, CPR_MAX_RESET, CPR_PERIOD, CPR_STEEPNESS,
)


class PartialReset:
    """Per-expert utility state and independent reset randomness.

    Supports a CPU Sequential(Linear, ReLU, Linear) expert.
    Bias parameters and optimizer moments are deliberately left unchanged.
    Event deltas measure CPR alone, excluding the preceding Adam update.
    """

    def __init__(self, model, *, seed):
        incoming, outgoing = model[0], model[2]
        if not isinstance(incoming, torch.nn.Linear):
            raise TypeError("Expected a linear input layer")
        if not isinstance(outgoing, torch.nn.Linear):
            raise TypeError("Expected a linear output layer")
        if incoming.out_features != outgoing.in_features:
            raise ValueError("Hidden dimensions do not match")
        if incoming.weight.device.type != "cpu":
            raise ValueError("Revision 1 implementation requires CPU experts")
        self.utility = torch.ones(
            incoming.out_features, dtype=incoming.weight.dtype)
        self.generator = torch.Generator(device="cpu")
        self.generator.manual_seed(seed)
        self.local_updates = 0
        self.pending_observation = False
        self.events = []

    def observe(self, model, per_example_losses):
        """Update utility from mean per-example L2 gradient norms.

        Losses must be unreduced noisy-label cross-entropies from this expert.
        autograd.grad leaves the optimizer's gradient buffers untouched.
        retain_graph permits the caller's ordinary mean-loss backward pass.
        """
        if self.pending_observation:
            raise RuntimeError("Previous observation has no optimizer-step completion")
        if per_example_losses.ndim != 1 or per_example_losses.numel() == 0:
            raise ValueError("Expected a nonempty vector of individual losses")
        if not torch.isfinite(per_example_losses).all():
            raise ValueError("Nonfinite per-example loss")
        incoming = model[0].weight
        if incoming.shape[0] != self.utility.numel():
            raise ValueError("Expert shape changed")
        norms = []
        for loss in per_example_losses.unbind():
            gradient, = torch.autograd.grad(loss, incoming, retain_graph=True)
            norms.append(torch.linalg.vector_norm(gradient.detach(), ord=2, dim=1))
        raw = torch.stack(norms).mean(dim=0)
        if not torch.isfinite(raw).all():
            raise ValueError("Nonfinite CPR utility")
        normalized = raw / (raw.mean() + CPR_EPSILON)
        with torch.no_grad():
            self.utility.mul_(CPR_EMA_DECAY).add_(
                normalized, alpha=1.0 - CPR_EMA_DECAY)
        self.pending_observation = True
        return raw.clone()

    def after_optimizer_step(self, model):
        """Advance local clock; every eighth completed update applies CPR."""
        if not self.pending_observation:
            raise RuntimeError("CPR requires a utility observation before each update")
        self.local_updates += 1
        self.pending_observation = False
        if self.local_updates % CPR_PERIOD:
            return None
        incoming, outgoing = model[0].weight, model[2].weight
        with torch.no_grad():
            before_in = incoming.detach().clone()
            before_out = outgoing.detach().clone()
            utility_before = self.utility.clone()
            fraction = CPR_MAX_RESET * torch.clamp(
                2.0 * torch.sigmoid(-CPR_STEEPNESS * (self.utility - 1.0)),
                max=1.0)
            # Same distribution as torch.nn.Linear's default input weights.
            bound = incoming.shape[1] ** -0.5
            target = torch.empty_like(incoming).uniform_(
                -bound, bound, generator=self.generator)
            incoming.mul_(1.0 - fraction[:, None]).add_(target * fraction[:, None])
            outgoing.mul_(1.0 - fraction[None, :])
            event = {
                "local_update": self.local_updates,
                "incoming_before": before_in,
                "incoming_after": incoming.detach().clone(),
                "outgoing_before": before_out,
                "outgoing_after": outgoing.detach().clone(),
                "utility": utility_before,
                "fraction": fraction.clone(),
                "incoming_delta_norm": torch.linalg.vector_norm(
                    incoming - before_in, ord=2, dim=1),
                "outgoing_delta_norm": torch.linalg.vector_norm(
                    outgoing - before_out, ord=2, dim=0),
                "incoming_before_norm": torch.linalg.vector_norm(
                    before_in, ord=2, dim=1),
                "outgoing_before_norm": torch.linalg.vector_norm(
                    before_out, ord=2, dim=0),
            }
            if not all(torch.isfinite(value).all() for value in event.values()
                       if isinstance(value, torch.Tensor)):
                raise ValueError("Nonfinite CPR intervention")
            self.utility.fill_(1.0)
        self.events.append(event)
        return copy.deepcopy(event)

    def state_dict(self):
        """Include local clock, EMA, independent RNG and intervention history."""
        return copy.deepcopy({
            "utility": self.utility,
            "rng_state": self.generator.get_state(),
            "local_updates": self.local_updates,
            "pending_observation": self.pending_observation,
            "events": self.events,
        })

    def load_state_dict(self, state):
        utility = state["utility"]
        if utility.shape != self.utility.shape or not torch.isfinite(utility).all():
            raise ValueError("Invalid checkpoint utility")
        if type(state["local_updates"]) is not int or state["local_updates"] < 0:
            raise ValueError("Invalid checkpoint local clock")
        self.utility = utility.detach().clone()
        self.generator.set_state(state["rng_state"].clone())
        self.local_updates = state["local_updates"]
        self.pending_observation = bool(state["pending_observation"])
        self.events = copy.deepcopy(state["events"])

    def activity(self, *, start_update, incoming_reference, outgoing_reference):
        """CPR path in the requested window, divided by PHASE-START norms.

        Both references must be the saved phase-start weights, including when
        start_update selects only the final 64 local updates of a control.
        The numerator window does not redefine the denominator in protocol
        section 5. This is neither net displacement nor behavioral benefit.
        """
        if (type(start_update) is not int
                or start_update < 0 or start_update > self.local_updates):
            raise ValueError("Invalid activity window start")
        if (incoming_reference.ndim != 2 or outgoing_reference.ndim != 2
                or incoming_reference.shape[0] != self.utility.numel()
                or outgoing_reference.shape[1] != self.utility.numel()):
            raise ValueError("Invalid phase-start reference shapes")
        if (not torch.isfinite(incoming_reference).all()
                or not torch.isfinite(outgoing_reference).all()):
            raise ValueError("Nonfinite phase-start reference")
        selected = [event for event in self.events
                    if start_update < event["local_update"] <= self.local_updates]
        in_sum = torch.zeros_like(self.utility)
        out_sum = torch.zeros_like(self.utility)
        for event in selected:
            in_sum += event["incoming_delta_norm"]
            out_sum += event["outgoing_delta_norm"]
        in_norm = torch.linalg.vector_norm(incoming_reference.detach(), ord=2, dim=1)
        out_norm = torch.linalg.vector_norm(outgoing_reference.detach(), ord=2, dim=0)
        in_ratio = in_sum / in_norm.clamp_min(CPR_EPSILON)
        out_ratio = out_sum / out_norm.clamp_min(CPR_EPSILON)
        return {
            "start_local_update": start_update,
            "end_local_update": self.local_updates,
            "intervention_count": len(selected),
            "incoming_path_norm": in_sum.tolist(),
            "outgoing_path_norm": out_sum.tolist(),
            "incoming_reference_norm": in_norm.tolist(),
            "outgoing_reference_norm": out_norm.tolist(),
            "incoming_relative_path": in_ratio.tolist(),
            "outgoing_relative_path": out_ratio.tolist(),
            "incoming_relative_path_median": float(torch.quantile(in_ratio, 0.5)),
            "outgoing_relative_path_median": float(torch.quantile(out_ratio, 0.5)),
            "quantile_levels": [0.0, 0.25, 0.5, 0.75, 1.0],
            "incoming_relative_path_quantiles": torch.quantile(
                in_ratio, in_ratio.new_tensor([0.0, 0.25, 0.5, 0.75, 1.0])).tolist(),
            "outgoing_relative_path_quantiles": torch.quantile(
                out_ratio, out_ratio.new_tensor([0.0, 0.25, 0.5, 0.75, 1.0])).tolist(),
            "zero_incoming_reference": (in_norm == 0).tolist(),
            "zero_outgoing_reference": (out_norm == 0).tolist(),
        }