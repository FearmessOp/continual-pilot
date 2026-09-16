"""Stationary control decisions from recorded results; no training on import."""
import math
from fractions import Fraction

import numpy as np

from .config import CPR_ACTIVITY_MINIMUM, EVALUATION_COUNT
from .gate_metrics import class_vector
from .schedule import cpr_event_count


REFERENCE_RUNS = {
    "B": {"primary": "A", "secondary": "A_expert1"},
    "D": {"primary": "C", "secondary": "C_expert1"},
}


def reference_comparison(method, *, system_predictions, reference_predictions, clean):
    """Compare against expert-zero full-update reference, not ideal frozen choice.

    reference_predictions must map recorded run names to their prediction arrays.
    D explicitly reuses C's array. The second initialization is descriptive only;
    it cannot replace the primary reference after results are seen.
    """
    if method not in REFERENCE_RUNS:
        raise ValueError("Only B and D have a stationary routed-system control")
    clean = class_vector(clean)
    system = class_vector(system_predictions)
    if len(clean) != EVALUATION_COUNT or system.shape != clean.shape:
        raise ValueError("System control requires 20000 paired evaluation examples")
    system_correct = int(np.sum(system == clean))
    comparisons = {}
    for role, name in REFERENCE_RUNS[method].items():
        reference = class_vector(reference_predictions[name])
        if reference.shape != clean.shape:
            raise ValueError("Reference evaluation shape mismatch")
        correct = int(np.sum(reference == clean))
        difference = correct - system_correct
        comparisons[role] = {
            "reference_run": name,
            "reference_correct": correct,
            "reference_accuracy": correct / len(clean),
            "reference_minus_system_correct": difference,
            "reference_minus_system_accuracy": difference / len(clean),
            "used_for_decision": role == "primary",
        }
    primary_difference = comparisons["primary"]["reference_minus_system_correct"]
    return {
        "method": method,
        "count": len(clean),
        "system_correct": system_correct,
        "system_accuracy": system_correct / len(clean),
        "comparisons": comparisons,
        "maximum_loss": 0.02,
        "passed": Fraction(primary_difference, len(clean)) <= Fraction(1, 50),
        "reference_is_independently_full_updated": True,
        "ideal_frozen_expert_selection_used_as_reference": False,
    }


def expert_usage(learner):
    """Snapshot routed usage without changing state or attributing causality."""
    learner._require_boundary()
    if learner.router is None:
        raise ValueError("Expert usage control requires a routed learner")
    rows = []
    for index, expert in enumerate(learner.experts):
        selected = learner.selected_groups[index]
        forced = learner.forced_groups[index]
        greedy = learner.greedy_groups[index]
        if selected != forced + greedy or expert.updates != selected:
            raise AssertionError("Routed usage and local optimizer clocks disagree")
        rows.append({
            "expert": index,
            "selected_groups": selected,
            "forced_exploration_groups": forced,
            "greedy_groups": greedy,
            "local_optimizer_updates": expert.updates,
            "training_examples": expert.training_examples,
            "cpr_interventions": 0 if expert.cpr is None else len(expert.cpr.events),
        })
    if sum(row["selected_groups"] for row in rows) != learner.groups_completed:
        raise AssertionError("Expert selections do not cover all global groups")
    if learner.router.updates != learner.groups_completed:
        raise AssertionError("Router update count differs from group opportunities")
    return {
        "global_group_opportunities": learner.groups_completed,
        "router_updates": learner.router.updates,
        "experts": rows,
        "interpretation": (
            "Usage and accuracy diagnostics inform possible explanations; "
            "counts alone do not causally separate routing and update-splitting costs."
        ),
    }


def cpr_activity_control(cpr, *, phase_start_incoming, phase_start_outgoing):
    """Last 64 local updates, normalized by saved PHASE-START weight norms."""
    if cpr.local_updates < 64:
        raise ValueError("CPR activity control requires at least 64 local updates")
    start = cpr.local_updates - 64
    report = cpr.activity(
        start_update=start,
        incoming_reference=phase_start_incoming,
        outgoing_reference=phase_start_outgoing)
    expected = cpr_event_count(start, 64)
    numerical_fields = (
        "incoming_path_norm", "outgoing_path_norm",
        "incoming_reference_norm", "outgoing_reference_norm",
        "incoming_relative_path", "outgoing_relative_path",
        "incoming_relative_path_quantiles", "outgoing_relative_path_quantiles",
    )
    finite = all(np.isfinite(report[key]).all() for key in numerical_fields)
    median = report["incoming_relative_path_median"]
    finite = bool(finite and math.isfinite(median)
                  and math.isfinite(report["outgoing_relative_path_median"]))
    clock_ok = report["intervention_count"] == expected
    report.update({
        "required_window_local_updates": 64,
        "expected_intervention_count": expected,
        "event_count_matches_clock": clock_ok,
        "all_values_finite": finite,
        "minimum_incoming_relative_path_median": CPR_ACTIVITY_MINIMUM,
        "passed": bool(finite and clock_ok and median >= CPR_ACTIVITY_MINIMUM),
        "denominator_boundary": "stationary_control_phase_start",
    })
    return report