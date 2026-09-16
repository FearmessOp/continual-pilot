"""Line 1 impact-window EXPLORATION on the ungated v0.3 student.

EXPLORATION, NOT a hypothesis test: the learnability gate was NOT passed.
Measures forgetting/recovery on a fixed, ungated student across four phases,
against each method's OWN phase-2 reference. Does not change the student,
generator, acceptance criterion or gate formula. Does not run Line 2 (v0.4).

Paired A vs replay: identical initial weights (deepcopy) and identical noisy
stream per training seed. Three frozen copies (end of phases 2, 3, 4) are
evaluated on one independent M2/R1 stream. Persists weights, per-example
predictions and integrity hashes; loads them back to verify.
"""
import argparse
import copy
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import torch
from torch import nn

import diagnose
import diagnose_v02 as diagnostics
from pilot import Reservoir
from generator_v03 import GeneratorV03

CLASSES = 4
PHASES = 4
LABEL = ("Learnability gate NOT passed; this run is an impact-window "
         "EXPLORATION, not a hypothesis test.")

PROTOCOL = {
    "generator_seed": 1000,
    "alpha": 0.5,
    "noise": 0.05,
    "generator_calibration_count": 20000,
    "hidden": 64,
    "input_dimension": 32,
    "model_seed": 7,
    "learning_rate": 0.001,
    "minibatch": 16,
    "phase_length": 40000,
    "capacity": 512,
    "replay_batch": 8,
    "training_seeds": [220001, 220002, 220003],
    "eval_history_seed": 221000,
    "eval_stream_seed": 221001,
    "eval_count": 20000,
    "transition_window": 1000,
    "block": 1000,
    "schedule": [(0, 0), (1, 0), (1, 1), (1, 0)],  # R1/M1, R1/M2, R2/M2, R1/M2.
}


def digest_array(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def make_model(hidden):
    return nn.Sequential(nn.Linear(32, hidden), nn.ReLU(), nn.Linear(hidden, 4))


def phase_stream(generator, seed):
    """Four-phase stream: schedule of (mixture, rule); 32-dim inputs only."""
    rng = np.random.default_rng(seed)
    parts = []
    for mixture, rule in PROTOCOL["schedule"]:
        x, noisy, clean, _ = generator.sample(
            PROTOCOL["phase_length"], mixture, rule, rng)
        parts.append((x, noisy, clean))
    return tuple(np.concatenate([p[i] for p in parts]) for i in range(3))


def evaluation_stream(generator):
    """Independent M2/R1 evaluation inputs, clean and noisy labels."""
    rng = np.random.default_rng(PROTOCOL["eval_stream_seed"])
    # Warm draw kept for parity with other evaluators' stream discipline.
    _ = generator.sample(64 * 4, 1, 0, np.random.default_rng(
        PROTOCOL["eval_history_seed"]))
    x, noisy, clean, _ = generator.sample(
        PROTOCOL["eval_count"], 1, 0, rng)
    return x, clean, noisy


def frozen_accuracy(model, eval_x, clean):
    """Clean accuracy of a frozen model on the shared M2/R1 stream."""
    model.eval()
    with torch.no_grad():
        logits = model(torch.from_numpy(eval_x))
        predictions = logits.argmax(dim=1).numpy()
    return float(np.mean(predictions == clean)), predictions


def run_method(generator, stream, *, replay, initial, eval_x, eval_clean):
    """Prequential four-phase run; snapshot frozen copies at phase ends."""
    model = copy.deepcopy(initial)
    optimizer = torch.optim.Adam(model.parameters(),
                                 lr=PROTOCOL["learning_rate"])
    buffer = Reservoir(PROTOCOL["capacity"] if replay else 0, 32,
                       seed=990000)
    x, noisy, clean = stream
    total = len(noisy)
    predictions = np.empty(total, dtype=np.int64)
    phase_length = PROTOCOL["phase_length"]
    minibatch = PROTOCOL["minibatch"]
    pending_x, pending_y = [], []
    steps = 0
    transition_updates = 0
    phase4_start = 3 * phase_length
    phase4_window_end = phase4_start + PROTOCOL["transition_window"]
    frozen = {}

    def flush():
        nonlocal steps
        if not pending_y:
            return
        model.train()
        batch_x = torch.from_numpy(np.stack(pending_x))
        batch_y = torch.from_numpy(np.array(pending_y))
        optimizer.zero_grad(set_to_none=True)
        nn.functional.cross_entropy(model(batch_x), batch_y).backward()
        optimizer.step()
        steps += 1
        pending_x.clear()
        pending_y.clear()

    for t in range(total):
        features = x[t]
        model.eval()
        with torch.no_grad():
            predictions[t] = int(model(torch.from_numpy(features)
                                       .unsqueeze(0)).argmax(dim=1).item())
        old_x, old_y = buffer.sample(PROTOCOL["replay_batch"] if replay else 0)
        pending_x.append(features)
        pending_y.append(noisy[t])
        for j in range(len(old_x)):  # Replay samples join the pending group.
            pending_x.append(old_x[j])
            pending_y.append(int(old_y[j]))
        # Update once every `minibatch` NEW examples, matching the gate cadence.
        if (t + 1) % minibatch == 0:
            in_window = phase4_start <= t < phase4_window_end
            flush()
            if in_window:
                transition_updates += 1
        if replay:
            buffer.add(features, noisy[t])
        # Snapshot frozen copies exactly at phase boundaries (after update).
        if (t + 1) % phase_length == 0:
            flush()  # Ensure no pending group crosses the boundary.
            phase = (t + 1) // phase_length
            if phase in (2, 3, 4):
                frozen[phase] = copy.deepcopy(model).eval()
    flush()

    accuracies = {}
    frozen_predictions = {}
    for phase, snapshot in frozen.items():
        accuracy, preds = frozen_accuracy(snapshot, eval_x, eval_clean)
        accuracies[phase] = accuracy
        frozen_predictions[phase] = preds

    # D_1000: phase-4 first window, learning model vs its OWN phase-2 frozen copy.
    window = slice(phase4_start, phase4_window_end)
    phase4_online = predictions[window]
    window_clean = clean[window]
    phase2_frozen = frozen[2]
    phase2_window_x = x[window]
    with torch.no_grad():
        phase2_window_pred = phase2_frozen(
            torch.from_numpy(phase2_window_x)).argmax(dim=1).numpy()
    d1000 = int(np.sum(phase4_online != window_clean)
                - np.sum(phase2_window_pred != window_clean))

    return {
        "model": model,
        "predictions": predictions,
        "frozen": frozen,
        "frozen_predictions": frozen_predictions,
        "frozen_m2r1_accuracy": accuracies,
        "damage_phase2_minus_phase3": accuracies[2] - accuracies[3],
        "recovery_phase4_minus_phase3": accuracies[4] - accuracies[3],
        "d1000": d1000,
        "optimizer_steps": steps,
        "transition_window_updates": transition_updates,
    }


def phase_regret(predictions, stream):
    """Secondary: per-phase oracle regret (unchanged oracle definition)."""
    _, noisy, clean = stream
    error = (predictions != noisy).astype(np.int64)
    oracle = (clean != noisy).astype(np.int64)
    regret = error - oracle
    result = []
    for phase in range(PHASES):
        start = phase * PROTOCOL["phase_length"]
        stop = start + PROTOCOL["phase_length"]
        result.append({
            "phase": phase + 1,
            "first_1000_regret": int(regret[start:start + 1000].sum()),
            "total_regret": int(regret[start:stop].sum()),
        })
    return result


def save_records(directory, method, seed, run, stream):
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {"method": method, "seed": seed, "phase_weights": {}}
    for phase, snapshot in run["frozen"].items():
        path = directory / f"{method}_seed{seed}_phase{phase}.pt"
        torch.save(snapshot.state_dict(), path)
        manifest["phase_weights"][str(phase)] = {
            "file": path.name,
            "state_sha256": diagnose.state_digest(snapshot),
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    final_path = directory / f"{method}_seed{seed}_final.pt"
    torch.save(run["model"].state_dict(), final_path)
    manifest["final_state_sha256"] = diagnose.state_digest(run["model"])
    npz_path = directory / f"{method}_seed{seed}_predictions.npz"
    np.savez(npz_path, online_predictions=run["predictions"],
             **{f"frozen_pred_phase{p}": v
                for p, v in run["frozen_predictions"].items()})
    manifest["predictions_file"] = npz_path.name
    manifest["online_predictions_sha256"] = digest_array(run["predictions"])
    (directory / f"{method}_seed{seed}_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    with np.load(npz_path) as loaded:
        if digest_array(loaded["online_predictions"]) != \
                manifest["online_predictions_sha256"]:
            raise AssertionError("Impact record load mismatch; halting")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "results_impact_v03")
    args = parser.parse_args()
    output = args.output / "summary.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(PROTOCOL["model_seed"])

    generator = GeneratorV03(
        seed=PROTOCOL["generator_seed"], alpha=PROTOCOL["alpha"],
        noise=PROTOCOL["noise"],
        calibration_count=PROTOCOL["generator_calibration_count"])
    eval_x, eval_clean, eval_noisy = evaluation_stream(generator)

    report = {
        "revision": "line1-impact-v03",
        "label": LABEL,
        "protocol": {k: v for k, v in PROTOCOL.items()},
        "eval_clean_sha256": digest_array(eval_clean),
        "seeds": {},
        "limitations": [
            LABEL,
            "Three seeds; per-seed rows only, no confirmatory pooling.",
            "D1000 mixes forgetting and re-learning by design.",
            "Reference is each method's own phase-2 model, not an oracle.",
            "No router, renewal, Line 2 (v0.4) or gate change in this run.",
        ],
    }

    records_dir = args.output / "records"
    for seed in PROTOCOL["training_seeds"]:
        torch.manual_seed(PROTOCOL["model_seed"])
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(PROTOCOL["model_seed"])
            initial = make_model(PROTOCOL["hidden"])
        stream = phase_stream(generator, seed)
        seed_entry = {}
        for method, replay in (("A", False), ("replay", True)):
            run = run_method(generator, stream, replay=replay,
                             initial=initial, eval_x=eval_x,
                             eval_clean=eval_clean)
            save_records(records_dir, method, seed, run, stream)
            seed_entry[method] = {
                "frozen_m2r1_accuracy": {str(p): a for p, a
                                         in run["frozen_m2r1_accuracy"].items()},
                "damage_phase2_minus_phase3": run["damage_phase2_minus_phase3"],
                "recovery_phase4_minus_phase3": run["recovery_phase4_minus_phase3"],
                "d1000": run["d1000"],
                "optimizer_steps": run["optimizer_steps"],
                "transition_window_updates": run["transition_window_updates"],
                "phase_regret": phase_regret(run["predictions"], stream),
                "final_state_sha256": diagnose.state_digest(run["model"]),
            }
            print(f"seed={seed} {method}: D1000={run['d1000']}, "
                  f"damage={run['damage_phase2_minus_phase3']:.4f}, "
                  f"recovery={run['recovery_phase4_minus_phase3']:.4f}, "
                  f"transition_updates={run['transition_window_updates']}",
                  flush=True)
        seed_entry["shared_initial_state_sha256"] = diagnose.state_digest(initial)
        report["seeds"][str(seed)] = seed_entry

    report["environment"] = {
        "python": platform.python_version(), "numpy": np.__version__,
        "torch": torch.__version__, "device": "cpu"}
    args.output.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    print(f"Results: {output.resolve()}", flush=True)


if __name__ == "__main__":
    main()