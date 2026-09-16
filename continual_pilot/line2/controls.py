"""Stationary control execution on previously archived, paired datasets.

No sampling or execution on import. No duration, power or main experiment.
The outer runner handles prerequisites and stops after a failed control stage.
"""
import copy
import time

import numpy as np

from .config import EVALUATION_COUNT, TRAIN_COUNT
from .control_metrics import cpr_activity_control, expert_usage, reference_comparison
from .gate_metrics import classification, online_curve, stationary_gate
from .learner import Learner
from .records import tree_digest
from .training import train_recorded


RUN_METHODS = (
    ("A", "A"), ("C", "C"),
    ("A_expert1", "A"), ("C_expert1", "C"),
    ("B", "B"), ("D", "D"),
)


def control_learners(seeds):
    """Build paired controls without duplicate C/D-reference training."""
    learners = {}
    for name, method in RUN_METHODS:
        run_seeds = copy.deepcopy(seeds)
        if name.endswith("_expert1"):
            run_seeds["model0"] = seeds["model1"]
            run_seeds["cpr0"] = seeds["cpr1"]
        learners[name] = Learner(method, seeds=run_seeds)
    for name in ("A", "C", "B", "D"):
        actual = tree_digest(learners[name].experts[0].model.state_dict())
        expected = tree_digest(learners["A"].experts[0].model.state_dict())
        if actual != expected:
            raise AssertionError("Unpaired expert-zero initialization")
    for name in ("A_expert1", "C_expert1"):
        if tree_digest(learners[name].experts[0].model.state_dict()) != tree_digest(
                learners["D"].experts[1].model.state_dict()):
            raise AssertionError("Unpaired expert-one reference initialization")
    return learners


def frozen_control(records, directory, learner, evaluation):
    """Archive system and both-rule expert diagnostics without modifying state."""
    before = tree_digest(learner.checkpoint())
    x = evaluation["x"]
    predictions = learner.frozen_predictions(x)
    arrays = {"index": evaluation["index"], "system_predictions": predictions}
    expert_reports = []
    for index, expert in enumerate(learner.experts):
        if len(learner.experts) == 1:
            expert_predictions = predictions.copy()
        else:
            expert_predictions = np.asarray([
                int(expert.scores(row[None])[0].argmax()) for row in x
            ], dtype=np.int64)
        arrays[f"expert{index}_predictions"] = expert_predictions
        expert_reports.append({
            "expert": index,
            "R1": classification(expert_predictions, evaluation["r1"]),
            "R2": classification(expert_predictions, evaluation["r2"]),
        })
    if tree_digest(learner.checkpoint()) != before:
        raise AssertionError("Frozen control mutated learner state")
    records.arrays(f"{directory}/frozen.npz", arrays)
    return predictions, expert_reports


def run_stationary_condition(records, directory, *, seeds, training,
                             calibration, evaluation):
    """Run six unique stationary controls on the exact same recorded data.

    Dictionaries contain evaluator data. Only x/noisy are passed to training.
    Full-update CPR references also provide isolated ideal-D expert mechanics:
    an expert's update is independent of any inactive expert/router. Those
    reference records are reused, not counted as additional independent runs.
    Real B/D routing remains enabled throughout their own stationary training.
    """
    if len(training["noisy"]) != TRAIN_COUNT:
        raise ValueError("Stationary control requires 40000 training examples")
    if len(evaluation["clean"]) != EVALUATION_COUNT:
        raise ValueError("Stationary control requires 20000 evaluation examples")
    learners = control_learners(seeds)
    reports, predictions = {}, {}
    started = time.perf_counter()
    for name, _ in RUN_METHODS:
        learner = learners[name]
        path = f"{directory}/{name}"
        result = train_recorded(
            records, path, learner, x=training["x"], noisy=training["noisy"],
            verification_inputs=evaluation["x"][:16])
        prediction, experts = frozen_control(records, path, learner, evaluation)
        predictions[name] = prediction
        report = {
            "training": result["report"],
            "gate": stationary_gate(prediction, evaluation["clean"], calibration["clean"]),
            "learning_curve": online_curve(
                result["predictions"], training["noisy"], training["clean"]),
            "frozen_experts": experts,
            "usage": None if learner.router is None else expert_usage(learner),
            "activity": None,
        }
        if name in ("C", "C_expert1"):
            weights = result["phase_start_weights"]
            report["activity"] = cpr_activity_control(
                learner.experts[0].cpr,
                phase_start_incoming=weights["expert0_incoming"],
                phase_start_outgoing=weights["expert0_outgoing"])
        records.json(f"{path}/control_summary.json", report)
        reports[name] = report

    comparisons = {
        method: reference_comparison(
            method, system_predictions=predictions[method],
            reference_predictions=predictions, clean=evaluation["clean"])
        for method in ("B", "D")
    }
    required = {
        "A_learnability": reports["A"]["gate"]["passed"],
        "C_learnability": reports["C"]["gate"]["passed"],
        "ideal_D_expert0_learnability_reuses_C": reports["C"]["gate"]["passed"],
        "ideal_D_expert1_learnability": reports["C_expert1"]["gate"]["passed"],
        "C_activity": reports["C"]["activity"]["passed"],
        "ideal_D_expert0_activity_reuses_C": reports["C"]["activity"]["passed"],
        "ideal_D_expert1_activity": reports["C_expert1"]["activity"]["passed"],
        "B_stationary_loss": comparisons["B"]["passed"],
        "D_stationary_loss": comparisons["D"]["passed"],
    }
    summary = {
        "runs": reports,
        "system_reference_comparisons": comparisons,
        "required_checks": required,
        "passed": all(required.values()),
        "unique_training_runs": len(RUN_METHODS),
        "ideal_D_isolated_expert_record_aliases": {"0": "C", "1": "C_expert1"},
        "secondary_A_expert1_is_not_a_replacement_gate": True,
        "seconds_including_records_and_evaluation": time.perf_counter() - started,
        "next_action": "await_other_controls" if all(required.values()) else "stop_for_user",
    }
    records.json(f"{directory}/condition_summary.json", summary)
    return summary