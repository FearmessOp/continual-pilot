"""Recorded prequential training; no generator, clean labels or runs on import."""
import time

import numpy as np

from .config import MINIBATCH
from .records import tree_digest


def train_recorded(records, directory, learner, *, x, noisy, verification_inputs):
    """Train complete groups, archiving predictions and full boundary states.

    This routine receives no clean targets, rule identities or phase IDs.
    Verification inputs are used only for read-only checkpoint loading checks.
    The caller archives training/evaluation datasets and their RNG provenance
    before invoking this routine. No partial trailing group is silently dropped.
    """
    x = np.asarray(x)
    noisy = np.asarray(noisy)
    if (x.dtype != np.float32 or x.ndim != 2 or x.shape[1] != 32
            or not np.isfinite(x).all()):
        raise ValueError("Expected finite float32 training inputs")
    if (noisy.shape != (len(x),) or not len(noisy)
            or noisy.dtype.kind not in "iu"
            or np.any(noisy < 0) or np.any(noisy >= 4)
            or len(noisy) % MINIBATCH):
        raise ValueError("Expected complete groups of matching noisy class labels")
    learner._require_boundary()
    initial = learner.checkpoint()
    initial_digest = tree_digest(initial)
    initial_steps = [expert.updates for expert in learner.experts]
    initial_examples = [expert.training_examples for expert in learner.experts]
    initial_utility = [expert.utility_gradient_evaluations for expert in learner.experts]
    initial_router_steps = 0 if learner.router is None else learner.router.updates
    first_index = learner.examples_seen
    first_group = learner.groups_completed + 1
    records.checkpoint(
        f"{directory}/initial.pt", learner, verification_inputs=verification_inputs)
    phase_reference = {
        f"expert{i}_{direction}": expert.model[layer].weight.detach().clone()
        for i, expert in enumerate(learner.experts)
        for direction, layer in (("incoming", 0), ("outgoing", 2))
    }
    records.state(f"{directory}/phase_start_weights.pt", phase_reference)

    predictions = np.empty(len(x), dtype=np.int64)
    group_count = len(x) // MINIBATCH
    selected = np.full(group_count, -1, dtype=np.int64)
    forced = np.full(group_count, -1, dtype=np.int64)
    greedy = np.full(group_count, -1, dtype=np.int64)
    updated = np.zeros(group_count, dtype=bool)
    router_targets = np.full(group_count, -1, dtype=np.int64)
    summaries = np.zeros((group_count, 132), dtype=np.float32)
    # Explicit validity masks avoid NaN sentinels in numerical records.
    router_valid = np.zeros(group_count, dtype=bool)
    router_losses = np.zeros(group_count, dtype=np.float64)
    expert_losses = np.zeros((group_count, 2), dtype=np.float64)
    update_losses = np.zeros(group_count, dtype=np.float64)
    utility_valid = np.zeros(group_count, dtype=bool)
    raw_utilities = np.zeros((group_count, 64), dtype=np.float64)
    batch_counts = np.zeros(group_count, dtype=np.int64)
    replay_indices = []
    replay_offsets = [0]
    completed = 0
    start = time.perf_counter()
    for index, (row, label) in enumerate(zip(x, noisy)):
        predictions[index] = learner.predict(row)
        result = learner.observe(label)
        if result["index"] != first_index + index:
            raise AssertionError("Recorded online ordering differs from learner clock")
        replay_indices.extend(result["sampled_replay_indices"].tolist())
        replay_offsets.append(len(replay_indices))
        group = result["completed_group"]
        if group is None:
            continue
        if group["global_group"] != first_group + completed:
            raise AssertionError("Recorded group ordering differs from learner clock")
        for array, key in ((selected, "selected_expert"), (forced, "forced_expert"),
                           (greedy, "greedy_expert")):
            value = group[key]
            array[completed] = -1 if value is None else value
        updated[completed] = group["expert_updated"]
        summaries[completed] = group["group_start_summary"]
        if group["router"] is not None:
            router = group["router"]
            router_valid[completed] = True
            router_targets[completed] = router["target_expert"]
            router_losses[completed] = router["router_loss"]
            expert_losses[completed] = router["preupdate_mean_noisy_losses"]
        if group["expert_update"] is not None:
            update = group["expert_update"]
            update_losses[completed] = update["mean_noisy_loss"]
            batch_counts[completed] = update["training_examples"]
            if update["raw_utility"] is not None:
                utility_valid[completed] = True
                raw_utilities[completed] = update["raw_utility"]
        completed += 1
    training_seconds = time.perf_counter() - start
    learner._require_boundary()
    if completed != group_count:
        raise AssertionError("Incomplete training groups")
    records.arrays(f"{directory}/online.npz", {
        "index": np.arange(first_index, first_index + len(x), dtype=np.int64),
        "predictions": predictions,
        "sampled_replay_indices": np.asarray(replay_indices, dtype=np.int64),
        "sampled_replay_offsets": np.asarray(replay_offsets, dtype=np.int64),
    })
    records.arrays(f"{directory}/groups.npz", {
        "global_group": np.arange(first_group, first_group + group_count, dtype=np.int64),
        "selected_expert": selected, "forced_expert": forced, "greedy_expert": greedy,
        "expert_updated": updated, "group_start_summary": summaries,
        "router_valid": router_valid, "router_target": router_targets,
        "router_loss": router_losses, "preupdate_expert_noisy_losses": expert_losses,
        "update_loss": update_losses, "training_examples": batch_counts,
        "utility_valid": utility_valid, "raw_utility": raw_utilities,
    })
    records.checkpoint(
        f"{directory}/final.pt", learner, verification_inputs=verification_inputs)
    final_digest = tree_digest(learner.checkpoint())
    steps = [expert.updates - before
             for expert, before in zip(learner.experts, initial_steps)]
    examples = [expert.training_examples - before
                for expert, before in zip(learner.experts, initial_examples)]
    utility_evaluations = [
        expert.utility_gradient_evaluations - before
        for expert, before in zip(learner.experts, initial_utility)
    ]
    if sum(steps) != int(updated.sum()) or sum(examples) != int(batch_counts.sum()):
        raise AssertionError("Training accounting disagrees with expert counters")
    report = {
        "new_examples": len(x),
        "global_group_opportunities": group_count,
        "expert_optimizer_updates": steps,
        "router_optimizer_updates": (
            0 if learner.router is None else learner.router.updates - initial_router_steps),
        "training_examples_by_expert": examples,
        "cpr_per_example_gradient_evaluations": utility_evaluations,
        "sampled_replay_examples": len(replay_indices),
        "maximum_training_batch": int(batch_counts.max()),
        "training_seconds_including_online_bookkeeping": training_seconds,
        "initial_state_sha256": initial_digest,
        "final_state_sha256": final_digest,
        "checkpoint_reload_verified": True,
        "timing_excludes_artifact_writes_and_frozen_evaluation": True,
    }
    records.json(f"{directory}/training_summary.json", report)
    return {"predictions": predictions, "report": report,
            "phase_start_weights": phase_reference}