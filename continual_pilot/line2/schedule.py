"""Revision-1 group schedules; no training or random state on import."""
from .config import EXPLORATION_PERIOD, MINIBATCH


def _positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive Python integer")


def exploration_expert(global_group):
    """Forced expert at groups 8, 16, ...: 0, 1, ...; otherwise None.

    Group numbers are one-based and continue across phase boundaries.
    A returned zero is an expert index, not a false/no-exploration sentinel.
    """
    _positive_integer(global_group, "global_group")
    if global_group % EXPLORATION_PERIOD:
        return None
    return (global_group // EXPLORATION_PERIOD - 1) % 2


def update_due(global_group, *, rate_percent=100):
    """Deterministic phase-3/4 update policy for A and sparse-A controls.

    Sparse controls share A's full phase-1/2 training state. Callers must use
    rate_percent=100 during that preparation; no phase ID is needed here.
    Skipped groups are discarded, not accumulated for a later update.
    """
    _positive_integer(global_group, "global_group")
    if type(rate_percent) is not int or rate_percent not in (0, 25, 50, 75, 100):
        raise ValueError("rate_percent must be one of 0, 25, 50, 75, 100")
    if rate_percent == 0:
        return False
    if rate_percent == 25:
        return global_group % 4 == 0
    if rate_percent == 50:
        return global_group % 2 == 0
    if rate_percent == 75:
        return global_group % 4 != 0
    return True


def group_after(completed_examples):
    """Global group containing the next example; reject misaligned boundaries."""
    if type(completed_examples) is not int or completed_examples < 0:
        raise ValueError("completed_examples must be a nonnegative Python integer")
    if completed_examples % MINIBATCH:
        raise ValueError("Phase boundary must align with the minibatch")
    return completed_examples // MINIBATCH + 1


def window_schedule(completed_examples, count, *, rate_percent=100):
    """Report opportunity/actual-update counts and the secondary D480 mask.

    The mask removes samples in forced-exploration groups for ALL methods.
    It does not undo the effect of previous exploration on learned weights.
    Only complete aligned windows are accepted, as required by the protocol.
    """
    first_group = group_after(completed_examples)
    _positive_integer(count, "count")
    if count % MINIBATCH:
        raise ValueError("Window must contain complete minibatches")
    groups = list(range(first_group, first_group + count // MINIBATCH))
    forced = [exploration_expert(group) for group in groups]
    updates = [update_due(group, rate_percent=rate_percent) for group in groups]
    mask = [
        expert is None
        for expert in forced
        for _ in range(MINIBATCH)
    ]
    return {
        "global_groups": groups,
        "forced_experts": forced,
        "exploration_groups": [
            group for group, expert in zip(groups, forced) if expert is not None
        ],
        "update_groups": [group for group, due in zip(groups, updates) if due],
        "opportunities": len(groups),
        "actual_updates": sum(updates),
        "included_mask": mask,
        "included_count": sum(mask),
        "excluded_count": count - sum(mask),
    }


def cpr_event_count(start_local_updates, additional_updates, *, period=8):
    """Count CPR events without resetting an expert's local clock at a phase."""
    _positive_integer(period, "period")
    for name, value in (("start_local_updates", start_local_updates),
                        ("additional_updates", additional_updates)):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a nonnegative Python integer")
    return ((start_local_updates + additional_updates) // period
            - start_local_updates // period)