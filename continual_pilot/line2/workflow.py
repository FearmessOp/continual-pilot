"""Only the currently authorized acceptance and stationary-control stages.

The CLI must verify and archive protocol/addendum/source/test/environment
prerequisites BEFORE invoking this workflow. No execution occurs on import.
"""
import time

import numpy as np
import torch

from .config import CALIBRATION_COUNT, EVALUATION_COUNT, TRAIN_COUNT
from .controls import run_stationary_condition
from .data import learner_seeds, representation_data, stationary_data
from .pool import run_control_pool, save_trace
from .representation import block_summaries, fit_probe


def save_dataset(records, directory, dataset):
    """Keep inputs, full-precision latents, both targets, proposal trace and RNG."""
    records.arrays(f"{directory}/data.npz", dataset["arrays"])
    save_trace(records, directory, dataset["trace"])
    records.json(f"{directory}/provenance.json", dataset["provenance"])


def run_representation_control(records, directory, *, filtered, pair):
    """Independent train/test role streams; no learned-state transfer to B/D."""
    started = time.perf_counter()
    datasets, blocks = {}, {}
    for split in ("train", "test"):
        dataset = representation_data(
            filtered, section="control", pair=pair, split=split)
        save_dataset(records, f"{directory}/{split}", dataset)
        datasets[split] = dataset
        blocks[split] = block_summaries(
            dataset["arrays"]["x"], dataset["arrays"]["noisy_by_rule"])
        records.arrays(f"{directory}/{split}/blocks.npz", blocks[split])
    train_seeds = set(datasets["train"]["provenance"]["seeds"].values())
    test_seeds = set(datasets["test"]["provenance"]["seeds"].values())
    if not train_seeds.isdisjoint(test_seeds):
        raise AssertionError("Representation training/test seeds overlap")
    result = fit_probe(
        blocks["train"]["summaries"], blocks["train"]["regime_targets"],
        blocks["test"]["summaries"], blocks["test"]["regime_targets"])
    loaded = records.state(f"{directory}/probe.pt", result["state"])
    with torch.random.fork_rng(devices=[]):
        restored = torch.nn.Linear(132, 2)
    restored.load_state_dict(loaded["model"], strict=True)
    with torch.no_grad():
        predictions = restored(torch.from_numpy(
            blocks["test"]["summaries"])).argmax(dim=1).numpy()
    if not np.array_equal(predictions, result["predictions"]):
        raise AssertionError("Loaded representation probe predictions differ")
    records.arrays(f"{directory}/predictions.npz", {
        "predictions": result["predictions"],
        "regime_targets": blocks["test"]["regime_targets"],
        "block_indices": blocks["test"]["block_indices"],
        "training_losses": result["training_losses"],
    })
    report = {
        **result["report"],
        "independent_train_test_role_seeds": True,
        "checkpoint_prediction_reload_verified": True,
        "seconds_including_data_records_and_training": time.perf_counter() - started,
    }
    records.json(f"{directory}/summary.json", report)
    return report


def run_allowed_stages(records):
    """Stop at acceptance failure, a failed control, or completion of controls.

    Each stationary condition's six unique runs are completed for its diagnostic
    table. Its failed decision prevents starting another condition/pair. A
    numerical/recording exception propagates to the CLI for failure archiving;
    it is never reclassified as a rejected teacher or automatically retried.
    """
    started = time.perf_counter()
    acceptance, accepted = run_control_pool(records)
    report = {
        "scope": "acceptance_and_stationary_controls_only",
        "acceptance": acceptance,
        "controls": [],
        "passed": False,
        "duration_power_main_started": False,
        "next_action": "stop_for_user",
    }
    if not acceptance["accepted"]:
        report["stop_reason"] = "insufficient_accepted_generators"
    else:
        for item in accepted:
            pair = item["pair"]
            directory = f"controls/pair{pair}"
            seeds = learner_seeds("control", pair)
            records.json(f"{directory}/learner_seeds.json", seeds)
            pair_report = {
                "pair": pair, "teacher_seed": item["teacher_seed"],
                "conditions": [], "representation": None, "passed": False,
            }
            report["controls"].append(pair_report)
            for condition in (0, 1):
                datasets = {}
                for role, count in (
                        ("training", TRAIN_COUNT),
                        ("gate-calibration", CALIBRATION_COUNT),
                        ("evaluation", EVALUATION_COUNT)):
                    dataset = stationary_data(
                        item["filtered"], section="control", pair=pair,
                        role=role, condition=condition, count=count)
                    save_dataset(
                        records, f"{directory}/condition{condition}/data/{role}", dataset)
                    datasets[role] = dataset
                stream_seeds = [data["provenance"]["seed"] for data in datasets.values()]
                if len(set(stream_seeds)) != len(stream_seeds):
                    raise AssertionError("Stationary train/calibration/test seeds overlap")
                result = run_stationary_condition(
                    records, f"{directory}/condition{condition}", seeds=seeds,
                    training=datasets["training"]["arrays"],
                    calibration=datasets["gate-calibration"]["arrays"],
                    evaluation=datasets["evaluation"]["arrays"])
                pair_report["conditions"].append({"condition": condition, **result})
                if not result["passed"]:
                    report["stop_reason"] = "stationary_condition_failed"
                    break
            else:
                representation = run_representation_control(
                    records, f"{directory}/representation",
                    filtered=item["filtered"], pair=pair)
                pair_report["representation"] = representation
                pair_report["passed"] = representation["passed"]
                if not representation["passed"]:
                    report["stop_reason"] = "representation_control_failed"
            records.json(f"{directory}/summary.json", pair_report)
            if not pair_report["passed"]:
                break
        else:
            report["passed"] = True
            report["stop_reason"] = "authorized_controls_completed_await_user_decision"
    report["seconds_including_records"] = time.perf_counter() - started
    records.json("summary.json", report)
    return report