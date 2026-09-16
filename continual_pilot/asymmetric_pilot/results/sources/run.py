"""Run the preregistered asymmetric pilot; never overwrite an existing run."""
import argparse
import json
import platform
import shutil
import sys
from pathlib import Path

import numpy as np
import torch

# Support direct invocation from the workspace root.
PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

import diagnose
from generator_v03 import GeneratorV03
from asymmetric_pilot.engine import (
    CONFIG, LABEL, Learner, frozen_report, make_evaluation, make_streams,
    phase_metrics, predict, prefix, select_candidate, tree_digest, window_metrics,
)


def file_digest(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Records:
    """Exclusive writes, round-trip verification, and a file integrity manifest."""

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=False)
        self.files = {}

    def arrays(self, name, arrays):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            np.savez_compressed(handle, **arrays)
        with np.load(path, allow_pickle=False) as loaded:
            if set(loaded.files) != set(arrays):
                raise AssertionError("Array archive keys differ")
            for key, value in arrays.items():
                if tree_digest(loaded[key]) != tree_digest(value):
                    raise AssertionError(f"Array round-trip mismatch: {name}/{key}")
        self.files[name] = {
            "sha256": file_digest(path),
            "arrays": {key: {"shape": list(value.shape), "dtype": str(value.dtype),
                             "state_sha256": tree_digest(value)}
                       for key, value in arrays.items()},
        }

    def checkpoint(self, name, learner):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        state = learner.checkpoint()
        with path.open("xb") as handle:
            torch.save(state, handle)
        loaded = torch.load(path, map_location="cpu", weights_only=True)
        restored = Learner.from_checkpoint(loaded)
        expected = tree_digest(state)
        if expected != tree_digest(restored.checkpoint()):
            raise AssertionError(f"Checkpoint round-trip mismatch: {name}")
        self.files[name] = {"sha256": file_digest(path),
                            "state_sha256": expected,
                            "model_sha256": diagnose.state_digest(learner.model)}
        return expected

    def json(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        self.files[name] = {"sha256": file_digest(path)}

    def finish(self):
        for name, entry in self.files.items():
            if file_digest(self.root / name) != entry["sha256"]:
                raise AssertionError(f"File changed during run: {name}")
        with (self.root / "manifest.json").open("x", encoding="utf-8") as handle:
            json.dump(self.files, handle, indent=2, allow_nan=False)


def save_phase(records, directory, phase, learner, result, data):
    records.arrays(f"{directory}/phase{phase}_online.npz", {
        "index": data["index"],
        "predictions": result["predictions"],
        "update_positions": result["update_positions"],
    })
    records.checkpoint(f"{directory}/phase{phase}_checkpoint.pt", learner)
    return phase_metrics(result, data)


def evaluate_and_save(records, directory, phase, learner, evaluation):
    report, predictions = frozen_report(learner, evaluation)
    records.arrays(f"{directory}/phase{phase}_frozen.npz",
                   {"index": evaluation["index"], "predictions": predictions})
    return report


def run_pilot(records, config):
    generator = GeneratorV03(
        seed=config["generator_seed"], alpha=config["alpha"],
        noise=config["noise"], calibration_count=config["calibration_count"])
    evaluation = make_evaluation(generator, config)
    records.arrays("data/evaluation.npz", evaluation)
    initial = diagnose.make_model(config["hidden"], False, seed=config["model_seed"])
    initial_digest = diagnose.state_digest(initial)
    rows = []
    validations = []
    window_count = config["window_updates"] * config["minibatch"]
    candidates = sorted(config["phase3_candidates"])

    for seed in config["stream_seeds"]:
        streams = make_streams(generator, seed, config)
        for phase, data in streams.items():
            records.arrays(f"data/seed{seed}_phase{phase}.npz", data)
        for method in ("A", "replay"):
            directory = f"seed{seed}/{method}"
            learner = Learner(
                initial, replay=method == "replay",
                reservoir_seed=seed + 4000, config=config)
            if diagnose.state_digest(learner.model) != initial_digest:
                raise AssertionError("Unpaired initial model")
            common_metrics = {}
            for phase in (1, 2):
                data = streams[str(phase)]
                result = learner.train_phase(data["x"], data["noisy"])
                common_metrics[str(phase)] = save_phase(
                    records, directory, phase, learner, result, data)
            frozen2 = evaluate_and_save(
                records, directory, 2, learner, evaluation)
            parent_digest = tree_digest(learner.checkpoint())
            reference = predict(learner.model, streams["4"]["x"][:window_count])
            records.arrays(f"{directory}/phase2_window_reference.npz", {
                "index": streams["4"]["index"][:window_count],
                "predictions": reference,
                "clean": streams["4"]["clean"][:window_count],
            })
            short_predictions = None
            for length in candidates:
                branch = learner.fork()
                branch_directory = f"{directory}/length{length}"
                data3 = prefix(streams["3"], length)
                result3 = branch.train_phase(data3["x"], data3["noisy"])
                if short_predictions is None:
                    short_predictions = result3["predictions"].copy()
                elif not np.array_equal(
                        short_predictions, result3["predictions"][:len(short_predictions)]):
                    raise AssertionError("Candidate phase-3 prefix predictions differ")
                metric3 = save_phase(
                    records, branch_directory, 3, branch, result3, data3)
                frozen3 = evaluate_and_save(
                    records, branch_directory, 3, branch, evaluation)
                data4 = streams["4"]
                result4 = branch.train_phase(data4["x"], data4["noisy"])
                metric4 = save_phase(
                    records, branch_directory, 4, branch, result4, data4)
                frozen4 = evaluate_and_save(
                    records, branch_directory, 4, branch, evaluation)
                window = window_metrics(
                    result4["predictions"], reference, data4["clean"],
                    result4["update_positions"], window_count)
                if window["updates"] != config["window_updates"]:
                    raise AssertionError("Transition update count differs from protocol")
                if tree_digest(learner.checkpoint()) != parent_digest:
                    raise AssertionError("Branch mutated phase-2 parent")
                row = {
                    "seed": seed, "method": method, "phase3_count": length,
                    "phase3_updates": metric3["optimizer_steps"],
                    "phase2_state_sha256": parent_digest,
                    "frozen": {"2": frozen2, "3": frozen3, "4": frozen4},
                    "damage": frozen2["r1_accuracy"] - frozen3["r1_accuracy"],
                    "recovery": frozen4["r1_accuracy"] - frozen3["r1_accuracy"],
                    "window": window,
                    "phases": {**common_metrics, "3": metric3, "4": metric4},
                    "total_optimizer_steps": branch.steps,
                }
                records.json(f"{branch_directory}/summary.json", row)
                rows.append(row)
                print(f"{seed} {method} L3={length}: "
                      f"damage={row['damage']:.5f}, "
                      f"D{window_count}={window['extra_errors']}, "
                      f"R2={frozen3['r2_accuracy']:.5f}", flush=True)
            validations.append({
                "seed": seed, "method": method,
                "parent_state_unchanged": True,
                "phase3_prefix_predictions_equal": True,
            })
    if diagnose.state_digest(initial) != initial_digest:
        raise AssertionError("Initial model mutated")
    return {
        "label": LABEL, "config": config, "rows": rows,
        "initial_state_sha256": initial_digest,
        "validations": validations, "selection": select_candidate(rows, config),
        "limitations": [
            "Three stream seeds; fixed teacher and fixed initial model.",
            "No learnability-gate pass, no confirmatory inference.",
            "Replay has extra memory and training compute.",
            "Selection is specific to this v0.3 pilot, not filtered v0.4.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=PROJECT / "asymmetric_pilot" / "results")
    args = parser.parse_args()
    records = Records(args.output)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    sources = [
        Path(__file__), Path(__file__).with_name("engine.py"),
        Path(__file__).with_name("PROTOCOL.md"),
        PROJECT / "pilot.py", PROJECT / "diagnose.py",
        PROJECT / "generator_v03.py",
    ]
    source_dir = records.root / "sources"
    source_dir.mkdir()
    for source in sources:
        destination = source_dir / source.name
        shutil.copyfile(source, destination)
        records.files[f"sources/{source.name}"] = {"sha256": file_digest(destination)}
    config = json.loads(json.dumps(CONFIG))
    records.json("protocol.json", config)
    report = run_pilot(records, config)
    report["environment"] = {
        "python": platform.python_version(), "numpy": np.__version__,
        "torch": torch.__version__, "device": "cpu", "threads": 1,
    }
    records.json("summary.json", report)
    records.finish()
    print(json.dumps(report["selection"]), flush=True)
    print(f"Results: {records.root.resolve()}", flush=True)


if __name__ == "__main__":
    main()