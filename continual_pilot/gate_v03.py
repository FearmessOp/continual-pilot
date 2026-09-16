"""Fixed v0.3 base-learner gate; capacity controls cannot replace the primary."""
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import torch

import diagnose
import diagnose_v02 as diagnostics
from generator_v03 import GeneratorV03


PROTOCOL = {
    "generator_seed": 1000,
    "alpha": 0.5,
    "noise": 0.05,
    "generator_calibration_count": 20000,
    "primary_hidden": 64,
    "capacity_controls": [128, 256],
    "model_seed": 7,
    "input_dimension": 32,
    "use_context": False,
    "context_window": 64,
    "learning_rate": 0.001,
    "minibatch": 16,
    "training_count": 40000,
    "training_seed": 120100,
    "baseline_seed": 120200,
    "baseline_count": 20000,
    "m1_evaluation_seed": 120300,
    "m2_evaluation_seed": 120400,
    "evaluation_count": 20000,
    "curve_block": 1000,
}


class MixtureView:
    """Select evaluation distribution without changing the underlying generator."""
    def __init__(self, generator, mixture):
        self.generator = generator
        self.mixture = mixture

    def sample(self, count, mixture, rule, rng):
        return self.generator.sample(count, self.mixture, rule, rng)


def decision(interval, threshold):
    low, high = interval
    if low > threshold:
        return "passed"
    if high < threshold:
        return "failed"
    return "indeterminate"


def evaluate(model, generator, *, mixture, seed, count):
    """Reuse frozen prequential evaluation; no context enters this base learner."""
    before = diagnose.state_digest(model)
    predictions, clean, noisy = diagnostics.frozen_evaluation(
        model, MixtureView(generator, mixture),
        use_context=False, context_window=PROTOCOL["context_window"],
        seed=seed, count=count)
    after = diagnose.state_digest(model)
    if before != after:
        raise AssertionError("Frozen evaluation changed model weights")
    correct = int(np.sum(predictions == clean))
    result = {
        "mixture": mixture,
        "rule": 0,
        "history_seed": seed,
        "stream_seed": seed + 1,
        "count": count,
        "frozen_clean_accuracy": correct / count,
        "frozen_noisy_accuracy": float(np.mean(predictions == noisy)),
        "oracle_noisy_accuracy": float(np.mean(clean == noisy)),
        "frozen_clean_wilson_95": list(diagnostics.wilson_interval(correct, count)),
        "weights_unchanged": True,
        "model_state_sha256": before,
        "clean_targets_sha256": hashlib.sha256(clean.tobytes()).hexdigest(),
        "noisy_targets_sha256": hashlib.sha256(noisy.tobytes()).hexdigest(),
    }
    result.update(diagnostics.classification_report(predictions, clean))
    return result


def run_gate(generator):
    p = PROTOCOL
    stream = diagnose.single_regime(
        generator, p["training_count"], p["training_seed"])
    baseline = diagnostics.majority_baseline(
        generator, seed=p["baseline_seed"], count=p["baseline_count"])
    threshold = diagnostics.gate_threshold(baseline)
    report = {
        "revision": "v03-base-gate",
        "protocol": dict(p),
        "baseline": baseline,
        "threshold": threshold,
        "nominal_gate_band": [0.925, 0.935],
        "controls": {},
        "limitations": [
            "One generator/training-seed pair; exploratory, not main experiment.",
            "Wilson intervals condition on trained weights and a measured threshold.",
            "Training-seed variation and threshold uncertainty are not included.",
            "Capacity controls never replace the preregistered 64-unit primary.",
            "No router, A+context, renewal, phase pilot or four-phase run.",
        ],
    }
    primary_model = None
    target_hashes = None
    for hidden in [p["primary_hidden"], *p["capacity_controls"]]:
        initial = diagnose.make_model(hidden, False, seed=p["model_seed"])
        model, _, predictions, steps, elapsed = diagnose.train_online(
            initial, stream, lr=p["learning_rate"], use_context=False,
            context_window=p["context_window"], minibatch=p["minibatch"],
            seed=p["model_seed"])
        frozen = evaluate(
            model, generator, mixture=0, seed=p["m1_evaluation_seed"],
            count=p["evaluation_count"])
        hashes = (frozen["clean_targets_sha256"], frozen["noisy_targets_sha256"])
        if target_hashes is not None and hashes != target_hashes:
            raise AssertionError("Capacity controls did not share evaluation targets")
        target_hashes = hashes
        entry = {
            "hidden": hidden,
            "role": "primary" if hidden == p["primary_hidden"] else "capacity_only",
            "parameters": sum(parameter.numel() for parameter in model.parameters()),
            "initial_state_sha256": diagnose.state_digest(initial),
            "optimizer_steps": steps,
            "training_seconds": elapsed,
            "online": diagnose.summarise(predictions, stream),
            "learning_curve": diagnostics.learning_curve(
                predictions, stream, block=p["curve_block"]),
            "evaluation": frozen,
            "gate_comparison": decision(frozen["frozen_clean_wilson_95"], threshold),
        }
        report["controls"][str(hidden)] = entry
        if hidden == p["primary_hidden"]:
            primary_model = model
        print(f"hidden={hidden}: clean={frozen['frozen_clean_accuracy']:.5f}, "
              f"CI={frozen['frozen_clean_wilson_95']}, "
              f"comparison={entry['gate_comparison']}", flush=True)
    primary = report["controls"][str(p["primary_hidden"])]
    report["gate_decision"] = primary["gate_comparison"]
    report["m2_evaluation"] = None
    if report["gate_decision"] == "passed":
        report["m2_evaluation"] = evaluate(
            primary_model, generator, mixture=1, seed=p["m2_evaluation_seed"],
            count=p["evaluation_count"])
    report["next_step"] = (
        "Preregister numerical phase-pilot criteria and module controls; no four phases yet."
        if report["gate_decision"] == "passed" else
        "Stop this gate round; do not promote a capacity control or change settings.")
    return report


def main():
    output = Path(__file__).parent / "results_gate_v03" / "summary.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    protocol_bytes = (Path(__file__).parent / "README.md").read_bytes()
    p = PROTOCOL
    generator = GeneratorV03(
        seed=p["generator_seed"], alpha=p["alpha"], noise=p["noise"],
        calibration_count=p["generator_calibration_count"])
    report = run_gate(generator)
    report["prerun_readme_sha256"] = hashlib.sha256(protocol_bytes).hexdigest()
    report["environment"] = {
        "python": platform.python_version(), "numpy": np.__version__,
        "torch": torch.__version__, "device": "cpu",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    print(f"Primary gate: {report['gate_decision']}; threshold={report['threshold']:.5f}")
    print(f"Results: {output.resolve()}")


if __name__ == "__main__":
    main()