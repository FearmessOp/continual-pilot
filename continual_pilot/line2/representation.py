"""Evaluator-only supervised regime probe from the approved implementation addendum.

No experimental streams are generated on import. Production callers must supply
independently seeded training/test streams and archive their complete provenance.
The probe state is never installed into a continual learner.
"""
import copy

import numpy as np
import torch
from torch import nn

from .config import CONTEXT_DIM, CONTEXT_WINDOW
from .expert import adam
from .memory import History


BLOCKS_PER_RULE = 512
PROBE_STEPS = 300


def block_summaries(x, noisy_by_rule):
    """One independent-history summary per nonoverlapping block and rule.

    Both rules share each raw input. Labels are separate noisy realizations.
    A fresh history per block prevents floating-point accumulation from previous
    blocks from leaking into otherwise disjoint summaries. No labels from the
    next block or from another rule enter the summary.
    """
    x = np.asarray(x)
    labels = np.asarray(noisy_by_rule)
    count = BLOCKS_PER_RULE * CONTEXT_WINDOW
    if (x.shape != (count, 32) or x.dtype != np.float32
            or not np.isfinite(x).all()):
        raise ValueError("Expected 32768 finite float32 shared input rows")
    if (labels.shape != (count, 2) or labels.dtype.kind not in "iu"
            or np.any(labels < 0) or np.any(labels >= 4)):
        raise ValueError("Expected two noisy rule labels for each shared input")
    summaries = np.empty((2 * BLOCKS_PER_RULE, CONTEXT_DIM), dtype=np.float32)
    targets = np.repeat(np.arange(2, dtype=np.int64), BLOCKS_PER_RULE)
    block_indices = np.tile(np.arange(BLOCKS_PER_RULE, dtype=np.int64), 2)
    for rule in (0, 1):
        for block in range(BLOCKS_PER_RULE):
            history = History()
            start = block * CONTEXT_WINDOW
            for index in range(start, start + CONTEXT_WINDOW):
                history.observe(x[index], labels[index, rule])
            summaries[rule * BLOCKS_PER_RULE + block] = history.summary()
    return {
        "summaries": summaries,
        "regime_targets": targets,
        "block_indices": block_indices,
        "start_indices": block_indices * CONTEXT_WINDOW,
        "stop_indices_exclusive": (block_indices + 1) * CONTEXT_WINDOW,
    }


def _probe_data(summaries, targets):
    x, y = np.asarray(summaries), np.asarray(targets)
    if (x.shape != (2 * BLOCKS_PER_RULE, CONTEXT_DIM)
            or x.dtype != np.float32 or not np.isfinite(x).all()):
        raise ValueError("Expected 1024 finite float32 summary rows")
    if (y.shape != (len(x),) or y.dtype.kind not in "iu"
            or np.any(y < 0) or np.any(y > 1)
            or not np.array_equal(np.bincount(y.astype(np.int64), minlength=2),
                                  [BLOCKS_PER_RULE, BLOCKS_PER_RULE])):
        raise ValueError("Expected exactly 512 regime targets per rule")
    return torch.from_numpy(x.copy()), torch.from_numpy(y.astype(np.int64, copy=True))


def probe_report(predictions, targets):
    prediction = np.asarray(predictions)
    targets = np.asarray(targets)
    for values in (prediction, targets):
        if (values.shape != (2 * BLOCKS_PER_RULE,) or values.dtype.kind not in "iu"
                or np.any(values < 0) or np.any(values > 1)):
            raise ValueError("Expected binary regime predictions and targets")
    support = np.bincount(targets.astype(np.int64), minlength=2)
    if not np.array_equal(support, [BLOCKS_PER_RULE, BLOCKS_PER_RULE]):
        raise ValueError("Both rules require exactly 512 independent test blocks")
    correct = [int(np.sum((prediction == targets) & (targets == r))) for r in (0, 1)]
    per_rule = [n / BLOCKS_PER_RULE for n in correct]
    # Equal supports make balanced and raw accuracy numerically equal, but both
    # are explicitly recorded. Exact count comparison includes the 90% boundary.
    passed = 10 * sum(correct) >= 9 * len(targets)
    return {
        "role": "evaluator_only_supervised_regime_representation_diagnostic",
        "test_blocks_per_rule": support.tolist(),
        "correct_blocks_per_rule": correct,
        "accuracy_per_rule": per_rule,
        "balanced_accuracy": sum(per_rule) / 2,
        "raw_accuracy": sum(correct) / len(targets),
        "required_balanced_accuracy": 0.90,
        "passed": passed,
        "weights_transferred_to_learner": False,
    }


def fit_probe(train_summaries, train_targets, test_summaries, test_targets):
    """Fixed 300 full-batch updates; never select epochs using test accuracy."""
    train_x, train_y = _probe_data(train_summaries, train_targets)
    test_x, test_y = _probe_data(test_summaries, test_targets)
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(0)
        model = nn.Linear(CONTEXT_DIM, 2)
    with torch.no_grad():
        model.weight.zero_()
        model.bias.zero_()
    optimizer = adam(model.parameters())
    losses = []
    for _ in range(PROBE_STEPS):
        optimizer.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(model(train_x), train_y)
        if not torch.isfinite(loss):
            raise ValueError("Nonfinite representation-probe training loss")
        loss.backward()
        if any(p.grad is None or not torch.isfinite(p.grad).all()
               for p in model.parameters()):
            raise ValueError("Invalid representation-probe gradient")
        optimizer.step()
        if any(not torch.isfinite(p).all() for p in model.parameters()):
            raise ValueError("Nonfinite representation-probe parameter")
        losses.append(float(loss.detach()))
    with torch.no_grad():
        predictions = model(test_x).argmax(dim=1).numpy().copy()
    state = copy.deepcopy({
        "schema": "line2-supervised-probe-v1",
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "gradients": [p.grad.detach().clone() for p in model.parameters()],
        "training": model.training,
        "updates": PROBE_STEPS,
        "training_rows_per_update": len(train_y),
    })
    return {
        "report": probe_report(predictions, test_y.numpy()),
        "predictions": predictions,
        "training_losses": np.asarray(losses, dtype=np.float64),
        "state": state,
    }