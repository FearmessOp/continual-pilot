"""Single-regime learnability diagnostics. Does NOT modify or rerun the four-phase pilot.

Every control changes exactly one thing from a shared reference so that an
accuracy gap can be attributed to that single change. Results are exploratory
single-seed measurements, not significance tests.
"""
import argparse
import copy
import json
import hashlib
from types import SimpleNamespace
import pilot
import platform
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from pilot import Context, Generator, tensor_bytes

CONTEXT_DIMENSION = 132  # 4 class frequencies + 4 class-conditional 32-d means.


def make_model(hidden, context, *, seed=7):
    """Seeded CPU initialization, isolated from probe/order RNG consumption."""
    width = 32 + (CONTEXT_DIMENSION if context else 0)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        return nn.Sequential(nn.Linear(width, hidden), nn.ReLU(), nn.Linear(hidden, 4))


def state_digest(model):
    """Record exact initial parameter bytes for same-shape comparisons."""
    digest = hashlib.sha256()
    for name, tensor in model.state_dict().items():
        digest.update(name.encode("utf-8"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def prediction_comparison(left, right):
    """Hard gate: exact dtype, shape and bytes, not just mean accuracy."""
    equal = (left.dtype == right.dtype and left.shape == right.shape
             and left.tobytes() == right.tobytes())
    if not equal:
        raise AssertionError("Prediction sequences differ; diagnostic aborted")
    return {
        "bitwise_equal": True,
        "count": int(left.size),
        "mismatches": 0,
        "sha256": hashlib.sha256(left.tobytes()).hexdigest(),
    }


def single_regime(generator, length, seed):
    """One stationary regime R1/M1; returns inputs, noisy labels, clean labels."""
    x, noisy, clean, _ = generator.sample(length, 0, 0, np.random.default_rng(seed))
    return x, noisy, clean


def encode(context, x, use_context):
    """Prediction-time feature. Never sees the current or any future label."""
    if not use_context:
        return x.astype(np.float32)
    return context.encode(x)


def train_online(model, stream, *, lr, use_context, context_window,
                 minibatch, seed):
    """Prequential online training. Predict before the label, then update.

    With minibatch > 1 the update is deferred to the end of each group, so the
    delayed-update and reduced-step-count effects stay visible in the metrics.
    """
    model = copy.deepcopy(model)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    context = Context(context_window)
    x, y, clean = stream
    predictions = np.empty(len(y), dtype=np.int64)
    pending_features, pending_labels = [], []
    steps = 0
    start = time.perf_counter()
    for t in range(len(y)):
        features = encode(context, x[t], use_context)
        model.eval()
        with torch.no_grad():
            logits = model(torch.from_numpy(features).unsqueeze(0))
            predictions[t] = int(logits.argmax(dim=1).item())
        pending_features.append(features)
        pending_labels.append(y[t])
        if len(pending_labels) == minibatch:
            model.train()
            batch_x = torch.from_numpy(np.stack(pending_features))
            batch_y = torch.from_numpy(np.array(pending_labels))
            optimizer.zero_grad(set_to_none=True)
            nn.functional.cross_entropy(model(batch_x), batch_y).backward()
            optimizer.step()
            steps += 1
            pending_features.clear()
            pending_labels.clear()
        context.observe(x[t], y[t])
    # Never drop a partial trailing group; otherwise late data would be unused.
    if pending_labels:
        model.train()
        batch_x = torch.from_numpy(np.stack(pending_features))
        batch_y = torch.from_numpy(np.array(pending_labels))
        optimizer.zero_grad(set_to_none=True)
        nn.functional.cross_entropy(model(batch_x), batch_y).backward()
        optimizer.step()
        steps += 1
    elapsed = time.perf_counter() - start
    return model, context, predictions, steps, elapsed


def frozen_accuracy(model, generator, *, use_context, context_window, seed):
    """Freeze weights, then measure on a fresh single-regime evaluation stream.

    The evaluation context is warmed from an independent prior history so the
    summary reflects genuine test-time conditions rather than training order.
    Evaluation data never enters any weight update.
    """
    warm_x, warm_y, _ = single_regime(generator, context_window * 4, seed)
    context = Context(context_window)
    for i in range(len(warm_y)):
        context.observe(warm_x[i], warm_y[i])
    x, y, clean = single_regime(generator, 5000, seed + 1)
    model.eval()
    correct_noisy = correct_clean = 0
    with torch.no_grad():
        for t in range(len(y)):
            features = encode(context, x[t], use_context)
            prediction = int(model(torch.from_numpy(features)
                                   .unsqueeze(0)).argmax(dim=1).item())
            correct_noisy += prediction == y[t]
            correct_clean += prediction == clean[t]
            context.observe(x[t], y[t])
    return {"frozen_noisy_accuracy": correct_noisy / len(y),
            "frozen_clean_accuracy": correct_clean / len(y)}


def summarise(predictions, stream, tail=1000):
    _, y, clean = stream
    error = predictions != y
    oracle_error = clean != y
    return {
        "online_accuracy": float(np.mean(~error)),
        "online_clean_accuracy": float(np.mean(predictions == clean)),
        "oracle_accuracy": float(np.mean(~oracle_error)),
        "last_tail_accuracy": float(np.mean(~error[-tail:])),
        "total_regret": int(np.sum(error.astype(int) - oracle_error.astype(int))),
    }


def logistic_probe(features, labels, *, epochs=300, lr=0.05, seed=0):
    """Tiny multinomial logistic regression: can the summary reveal the regime?

    Train and test come from independent streams, so a chance-level score means
    this linear probe cannot separate the regimes, not that the summary is
    provably information-free.
    """
    torch.manual_seed(seed)
    x = torch.from_numpy(features.astype(np.float32))
    y = torch.from_numpy(labels.astype(np.int64))
    model = nn.Linear(x.shape[1], int(labels.max()) + 1)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    for _ in range(epochs):
        optimizer.zero_grad(set_to_none=True)
        nn.functional.cross_entropy(model(x), y).backward()
        optimizer.step()
    return model


def context_summary_probe(generator, *, context_window, seed):
    """Build R1 and R2 summaries over the SAME input distribution (M2).

    Independent histories per regime; the probe is trained on one pair of
    streams and evaluated on a disjoint pair.
    """
    def build(rule, stream_seed):
        rng = np.random.default_rng(stream_seed)
        x, _, _, _ = generator.sample(context_window * 8, 1, rule, rng)
        labels = generator.labels(x @ generator.w, rule)
        context = Context(context_window)
        rows = []
        for i in range(len(labels)):
            if i >= context_window:  # Only once the window is full.
                rows.append(context.encode(x[i])[32:])  # Summary part only.
            context.observe(x[i], labels[i])
        return np.array(rows, dtype=np.float32)

    train = [build(0, seed), build(1, seed + 1)]
    test = [build(0, seed + 2), build(1, seed + 3)]
    train_x = np.concatenate(train)
    train_y = np.concatenate([np.zeros(len(train[0])), np.ones(len(train[1]))])
    test_x = np.concatenate(test)
    test_y = np.concatenate([np.zeros(len(test[0])), np.ones(len(test[1]))])
    probe = logistic_probe(train_x, train_y, seed=seed)
    with torch.no_grad():
        prediction = probe(torch.from_numpy(test_x)).argmax(dim=1).numpy()
    return {
        "regime_probe_test_accuracy": float(np.mean(prediction == test_y)),
        "chance_level": 0.5,
        "test_examples": int(len(test_y)),
        "note": "Chance means this linear probe cannot separate regimes; "
                "not a proof that the summary is information-free.",
    }


def balance_diagnostic(generator, *, seed, count=20000):
    """Report class balance and rule disagreement WITHOUT changing the generator.

    Also reports the effect of an unbiased-teacher variant: subtracting each
    output dimension's mean over a calibration sample. This is measured only,
    not applied to any learning run.
    """
    rng = np.random.default_rng(seed)
    result = {}
    calibration = rng.normal(size=(20000, 2))
    biases = []
    for index in range(3):
        a, b, scale = generator.teachers[index]
        raw = np.tanh(calibration @ a) @ b
        centered = raw - raw.mean(axis=1, keepdims=True)
        biases.append((centered / scale).mean(axis=0))
    for mixture in range(2):
        _, _, clean, z = generator.sample(count, mixture, 0, rng)
        second = generator.labels(z, 1)

        def debiased_labels(rule):
            common = generator.component(z[:, :2], 0) - biases[0]
            specific_index = 1 if rule == 0 else 2
            columns = z[:, 2:4] if rule == 0 else z[:, 4:6]
            specific = generator.component(columns, specific_index) - biases[specific_index]
            return (generator.alpha * common + specific).argmax(axis=1)

        debiased = debiased_labels(0)
        result[f"M{mixture + 1}"] = {
            "R1_class_fractions": (np.bincount(clean, minlength=4) / count).tolist(),
            "disagreement": float(np.mean(clean != second)),
            "debiased_R1_class_fractions": (np.bincount(debiased, minlength=4) / count).tolist(),
            "debiased_min_class_fraction": float(np.bincount(debiased, minlength=4).min() / count),
        }
    return result


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--noise", type=float, default=0.05)
    parser.add_argument("--reference-length", type=int, default=10000)
    parser.add_argument("--long-length", type=int, default=40000)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--context-window", type=int, default=64)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "results_diagnose_init_fixed")
    args = parser.parse_args()
    if args.long_length < args.reference_length:
        parser.error("long-length must be >= reference-length")
    for name in ("reference_length", "context_window", "threads"):
        if getattr(args, name) < 1:
            parser.error(f"{name} must be positive")
    return args


def main():
    args = parse_args()
    torch.set_num_threads(args.threads)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(args.seed)
    generator = Generator(args.seed, args.alpha, args.noise)

    reference_seed = args.seed + 100
    reference = single_regime(generator, args.reference_length, reference_seed)
    # Extend the SAME stream so the long run's first block matches the reference.
    extra = args.long_length - args.reference_length
    long_stream = reference
    if extra:
        tail = single_regime(generator, extra, reference_seed + 1)
        long_stream = tuple(np.concatenate((reference[i], tail[i])) for i in range(3))

    controls = {
        "reference": dict(stream=reference, hidden=64, use_context=True, minibatch=1),
        "no_context": dict(stream=reference, hidden=64, use_context=False, minibatch=1),
        "hidden_128": dict(stream=reference, hidden=128, use_context=True, minibatch=1),
        "hidden_256": dict(stream=reference, hidden=256, use_context=True, minibatch=1),
        "minibatch_16": dict(stream=reference, hidden=64, use_context=True, minibatch=16),
        "long_40k": dict(stream=long_stream, hidden=64, use_context=True, minibatch=1),
    }

    # Reproduce only the stationary pilot run, never the four-phase experiment.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(args.seed)
        pilot_initial = pilot.make_model(64)
    pilot_args = SimpleNamespace(lr=args.lr, context_window=args.context_window,
                                 capacity=512, replay_batch=8, seed=args.seed, hidden=64)
    pilot_predictions = pilot.run(pilot_initial, reference, pilot_args)["predictions"]
    reference_predictions = None
    report = {
        "revision": "init-fix-only",
        "validation": {},
        "config": {key: str(value) if isinstance(value, Path) else value
                   for key, value in vars(args).items()},
        "environment": {"python": platform.python_version(), "torch": torch.__version__,
                        "numpy": np.__version__, "device": "cpu"},
        "protocol": [
            "Same-shaped controls have identical seeded initial parameters.",
            "Different shapes share a seed, not identical parameters.",
            "This revision changes initialization only; legacy clean-label probe remains non-comparable to noisy student context.",
            "No gate threshold or causal conclusion is assigned in this revision.",
            "no_context also reduces input width and parameter count.",
            "long_40k shares its first 10k examples with the reference.",
            "Prediction always precedes the label (prequential).",
            "Frozen accuracy uses a fresh evaluation stream, excluded from updates.",
            "Single seed, exploratory; not a significance test.",
            "Generator is NOT modified; debiasing is measured only.",
        ],
        "generator_balance": balance_diagnostic(generator, seed=args.seed + 900),
        "context_summary_probe": context_summary_probe(
            generator, context_window=args.context_window, seed=args.seed + 500),
        "controls": {},
    }

    for name, spec in controls.items():
        print(f"Running control {name}", flush=True)
        base = make_model(spec["hidden"], spec["use_context"], seed=args.seed)
        model, _, predictions, steps, elapsed = train_online(
            base, spec["stream"], lr=args.lr, use_context=spec["use_context"],
            context_window=args.context_window, minibatch=spec["minibatch"],
            seed=args.seed)
        if name == "reference":
            reference_predictions = predictions.copy()
            report["validation"]["reference_vs_pilot_health_A"] = prediction_comparison(
                predictions, pilot_predictions)
        if name == "long_40k":
            report["validation"]["long_prefix_vs_reference"] = prediction_comparison(
                predictions[:args.reference_length], reference_predictions)
        entry = summarise(predictions, spec["stream"])
        entry["initial_state_sha256"] = state_digest(base)
        entry.update(frozen_accuracy(
            model, generator, use_context=spec["use_context"],
            context_window=args.context_window, seed=args.seed + 700))
        entry.update({
            "hidden": spec["hidden"],
            "uses_context": spec["use_context"],
            "minibatch": spec["minibatch"],
            "stream_length": len(spec["stream"][1]),
            "optimizer_steps": steps,
            "parameters": sum(p.numel() for p in model.parameters()),
            "parameter_bytes": tensor_bytes(model.parameters()),
            "seconds": elapsed,
        })
        report["controls"][name] = entry
        print(f"{name}: online={entry['online_accuracy']:.4f} "
              f"frozen_clean={entry['frozen_clean_accuracy']:.4f} "
              f"oracle={entry['oracle_accuracy']:.4f}", flush=True)

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["validation"], indent=2), flush=True)
    probe = report["context_summary_probe"]["regime_probe_test_accuracy"]
    print(f"Regime probe test accuracy: {probe:.4f} (chance 0.5)")
    print(f"Results: {args.output.resolve()}")


if __name__ == "__main__":
    main()