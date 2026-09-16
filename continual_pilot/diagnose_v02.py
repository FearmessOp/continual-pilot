"""v0.2 combined single-regime run: no context + 40k examples + minibatch 16.

Reuses the pilot generator and the init-fixed diagnostic building blocks.
Does NOT modify pilot.py, diagnose.py, or rerun the four-phase experiment.
The combination of three calibration controls (drop context, more steps, less
noisy steps) is legitimate to merge; it is a single candidate reference, not a
per-factor causal claim. Single seed, exploratory; not a significance test.
"""
import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch

from pilot import Generator, Context
import diagnose

CLASSES = 4


def majority_baseline(generator, *, seed, count=20000):
    """Majority-class accuracy on an INDEPENDENT calibration stream (not eval).

    The gate threshold is derived from this baseline so it never peeks at the
    evaluation stream. Clean labels define the ceiling of 1.0.
    """
    x, _, clean = diagnose.single_regime(generator, count, seed)
    fractions = np.bincount(clean, minlength=CLASSES) / count
    majority = float(fractions.max())
    return {
        "calibration_count": count,
        "class_fractions": fractions.tolist(),
        "majority_class": int(fractions.argmax()),
        "majority_baseline_accuracy": majority,
    }


def gate_threshold(baseline, *, ceiling=1.0, fraction=0.9):
    """base + fraction * (ceiling - base) on the CLEAN scale."""
    base = baseline["majority_baseline_accuracy"]
    return base + fraction * (ceiling - base)


def wilson_interval(correct, total, *, z=1.96):
    """Two-sided Wilson score interval for a binomial proportion."""
    if total == 0:
        return (0.0, 1.0)
    phat = correct / total
    denom = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denom
    margin = (z * np.sqrt(phat * (1 - phat) / total
                          + z * z / (4 * total * total))) / denom
    return (float(center - margin), float(center + margin))


def frozen_evaluation(model, generator, *, use_context, context_window, seed,
                      count=20000):
    """Frozen-weight evaluation on a fresh stream; returns per-example vectors.

    Warms an independent prior context, then predicts each example before its
    label is observed. Evaluation data never enters any weight update. Returns
    predictions and both clean/noisy targets so paired tests can be computed.
    """
    warm_x, warm_y, _ = diagnose.single_regime(generator, context_window * 4, seed)
    context = Context(context_window)
    for i in range(len(warm_y)):
        context.observe(warm_x[i], warm_y[i])
    x, noisy, clean = diagnose.single_regime(generator, count, seed + 1)
    predictions = np.empty(count, dtype=np.int64)
    model.eval()
    with torch.no_grad():
        for t in range(count):
            features = diagnose.encode(context, x[t], use_context)
            predictions[t] = int(model(torch.from_numpy(features)
                                       .unsqueeze(0)).argmax(dim=1).item())
            context.observe(x[t], noisy[t])
    return predictions, clean, noisy


def classification_report(predictions, clean):
    """Per-class support, recall and a full confusion matrix on the clean rule."""
    confusion = np.zeros((CLASSES, CLASSES), dtype=np.int64)
    for true, pred in zip(clean, predictions):
        confusion[true, pred] += 1
    support = confusion.sum(axis=1)
    correct = np.diagonal(confusion)
    recall = np.where(support > 0, correct / np.maximum(support, 1), np.nan)
    return {
        "confusion_matrix_true_by_pred": confusion.tolist(),
        "class_support": support.tolist(),
        "per_class_recall": [None if s == 0 else float(r)
                             for s, r in zip(support, recall)],
    }


def learning_curve(predictions, stream, *, block=1000):
    """Online clean accuracy in non-overlapping blocks; reveals plateau vs rise."""
    _, _, clean = stream
    correct = (predictions == clean).astype(np.int64)
    rows = []
    for start in range(0, len(clean), block):
        stop = min(start + block, len(clean))
        rows.append({
            "block_end": stop,
            "count": stop - start,
            "online_clean_accuracy": float(np.mean(correct[start:stop])),
        })
    return rows


def paired_bootstrap(errors_a, errors_b, *, resamples=2000, seed=0):
    """Paired bootstrap CI for mean(errors_b - errors_a) on shared examples.

    Positive mean means b makes MORE errors than a. Resamples example indices,
    so it respects the pairing (same evaluation stream) rather than assuming
    independent single-model standard errors.
    """
    difference = errors_b.astype(np.int64) - errors_a.astype(np.int64)
    rng = np.random.default_rng(seed)
    count = len(difference)
    means = np.empty(resamples, dtype=np.float64)
    for i in range(resamples):
        ids = rng.integers(0, count, size=count)
        means[i] = difference[ids].mean()
    return {
        "observed_mean_difference": float(difference.mean()),
        "ci_low": float(np.percentile(means, 2.5)),
        "ci_high": float(np.percentile(means, 97.5)),
        "note": "difference = combined_errors - reference_errors on clean rule; "
                "positive favors reference, negative favors combined.",
    }


def summary_probe(generator, *, context_window, seed, use_4freq_only):
    """Regime probe on NOISY-label summaries; matches what the student sees.

    Windows overlap, so effective independent observations are far fewer than
    the raw row count; this is reported explicitly. Train and test are disjoint
    streams. Optionally restricts the summary to the 4 class frequencies.
    """
    def build(rule, stream_seed):
        rng = np.random.default_rng(stream_seed)
        x, noisy, _, _ = generator.sample(context_window * 8, 1, rule, rng)
        context = Context(context_window)
        rows = []
        for i in range(len(noisy)):
            if i >= context_window:  # Only once the window is full.
                summary = context.encode(x[i])[32:]  # Drop the raw input part.
                rows.append(summary[:CLASSES] if use_4freq_only else summary)
            context.observe(x[i], noisy[i])  # NOISY label, as the student uses.
        return np.array(rows, dtype=np.float32)

    train = [build(0, seed), build(1, seed + 1)]
    test = [build(0, seed + 2), build(1, seed + 3)]
    train_x = np.concatenate(train)
    train_y = np.concatenate([np.zeros(len(train[0])), np.ones(len(train[1]))])
    test_x = np.concatenate(test)
    test_y = np.concatenate([np.zeros(len(test[0])), np.ones(len(test[1]))])
    probe = diagnose.logistic_probe(train_x, train_y, seed=seed)
    with torch.no_grad():
        prediction = probe(torch.from_numpy(test_x)).argmax(dim=1).numpy()
    return {
        "feature_dimension": int(train_x.shape[1]),
        "regime_probe_test_accuracy": float(np.mean(prediction == test_y)),
        "chance_level": 0.5,
        "raw_test_rows": int(len(test_y)),
        "distinct_windows_per_stream": int(len(test[0])),
        "effective_independent_blocks_estimate": int(2 * len(test[0])
                                                     // context_window),
        "note": "Windows overlap; raw rows overstate independence. Uses NOISY "
                "labels to match the student. Chance means this linear probe "
                "cannot separate regimes here, not that the summary is empty.",
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--noise", type=float, default=0.05)
    parser.add_argument("--length", type=int, default=40000)
    parser.add_argument("--minibatch", type=int, default=16)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--context-window", type=int, default=64)
    parser.add_argument("--eval-count", type=int, default=20000)
    parser.add_argument("--block", type=int, default=1000)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "results_v02")
    args = parser.parse_args()
    for name in ("length", "minibatch", "hidden", "context_window",
                 "eval_count", "block", "threads"):
        if getattr(args, name) < 1:
            parser.error(f"{name} must be positive")
    if not (0 <= args.noise < 0.75) or args.alpha < 0 or args.lr <= 0:
        parser.error("Require 0 <= noise < .75, alpha >= 0 and lr > 0")
    return args


def train_and_evaluate(generator, spec, args):
    """Train one control, then run the shared 20k frozen evaluation on it."""
    base = diagnose.make_model(spec["hidden"], spec["use_context"], seed=args.seed)
    model, _, predictions, steps, elapsed = diagnose.train_online(
        base, spec["stream"], lr=args.lr, use_context=spec["use_context"],
        context_window=args.context_window, minibatch=spec["minibatch"],
        seed=args.seed)
    eval_predictions, eval_clean, eval_noisy = frozen_evaluation(
        model, generator, use_context=spec["use_context"],
        context_window=args.context_window, seed=args.seed + 700,
        count=args.eval_count)
    clean_correct = int(np.sum(eval_predictions == eval_clean))
    noisy_correct = int(np.sum(eval_predictions == eval_noisy))
    low, high = wilson_interval(clean_correct, args.eval_count)
    entry = {
        "hidden": spec["hidden"],
        "uses_context": spec["use_context"],
        "minibatch": spec["minibatch"],
        "stream_length": len(spec["stream"][1]),
        "optimizer_steps": steps,
        "initial_state_sha256": diagnose.state_digest(base),
        "training_seconds": elapsed,
        "frozen_clean_accuracy": clean_correct / args.eval_count,
        "frozen_noisy_accuracy": noisy_correct / args.eval_count,
        "frozen_clean_wilson_95": [low, high],
        "eval_count": args.eval_count,
    }
    entry.update(classification_report(eval_predictions, eval_clean))
    return entry, model, eval_predictions, eval_clean


def main():
    args = parse_args()
    torch.set_num_threads(args.threads)
    torch.use_deterministic_algorithms(True)
    generator = Generator(args.seed, args.alpha, args.noise)

    reference_seed = args.seed + 100
    reference_stream = diagnose.single_regime(generator, 10000, reference_seed)
    extra = args.length - 10000
    long_stream = reference_stream
    if extra > 0:
        tail = diagnose.single_regime(generator, extra, reference_seed + 1)
        long_stream = tuple(np.concatenate((reference_stream[i], tail[i]))
                            for i in range(3))
    elif extra < 0:
        long_stream = tuple(array[:args.length] for array in reference_stream)

    controls = {
        # Reference matches the init-fixed diagnostic: with context, 10k, mb 1.
        "reference": dict(stream=reference_stream, hidden=args.hidden,
                          use_context=True, minibatch=1),
        # The combined v0.2 candidate: no context + 40k + minibatch 16.
        "combined": dict(stream=long_stream, hidden=args.hidden,
                         use_context=False, minibatch=args.minibatch),
    }

    baseline = majority_baseline(generator, seed=args.seed + 800,
                                 count=args.eval_count)
    gate = gate_threshold(baseline)

    report = {
        "revision": "v0.2-combined",
        "config": {key: str(value) if isinstance(value, Path) else value
                   for key, value in vars(args).items()},
        "environment": {"python": platform.python_version(),
                        "torch": torch.__version__, "numpy": np.__version__,
                        "device": "cpu"},
        "protocol": [
            "Combined candidate merges three calibration controls; not a "
            "per-factor causal decomposition.",
            "Gate threshold uses majority baseline from an INDEPENDENT "
            "calibration stream, never the evaluation stream.",
            "Frozen clean accuracy is the single gate metric on the clean scale.",
            "Wilson 95% interval reported; if it straddles the gate the "
            "result is INDETERMINATE with one seed.",
            "Paired bootstrap compares combined vs reference on the SHARED "
            "evaluation stream; single-model SE is not used.",
            "Evaluation distribution is M1 (learnability). If the gate is "
            "passed, an M2 frozen accuracy must also be reported before "
            "returning to the four-phase experiment.",
            "Combined gain need not be additive: long_40k's benefit came from "
            "40k steps; minibatch 16 yields only length/16 steps. Read the "
            "curve as a step-count vs step-noise trade-off, not a refutation.",
            "Single seed, exploratory; not a significance test.",
            "Generator is NOT modified. Four-phase experiment NOT rerun.",
        ],
        "generator_balance": diagnose.balance_diagnostic(
            generator, seed=args.seed + 900),
        "gate": {
            "metric": "frozen_clean_accuracy",
            "calibration_majority_baseline": baseline,
            "ceiling": 1.0,
            "fraction": 0.9,
            "threshold": gate,
            "formula": "base + 0.9 * (1.0 - base) on the clean scale",
        },
        "summary_probe_full_noisy": summary_probe(
            generator, context_window=args.context_window, seed=args.seed + 500,
            use_4freq_only=False),
        "summary_probe_4freq_noisy": summary_probe(
            generator, context_window=args.context_window, seed=args.seed + 600,
            use_4freq_only=True),
        "controls": {},
        "learning_curve_combined": [],
        "paired_bootstrap_combined_vs_reference": {},
        "gate_decision": {},
    }

    stored = {}
    for name, spec in controls.items():
        print(f"Running control {name}", flush=True)
        entry, model, predictions, clean = train_and_evaluate(
            generator, spec, args)
        report["controls"][name] = entry
        stored[name] = (predictions, clean)
        print(f"{name}: frozen_clean={entry['frozen_clean_accuracy']:.4f} "
              f"wilson={entry['frozen_clean_wilson_95']}", flush=True)

    combined_predictions, combined_clean = stored["combined"]
    reference_predictions, reference_clean = stored["reference"]
    # Both evaluated on the same frozen stream (same seed), so pairing holds.
    report["learning_curve_combined"] = learning_curve(
        diagnose.train_online(
            diagnose.make_model(args.hidden, False, seed=args.seed),
            long_stream, lr=args.lr, use_context=False,
            context_window=args.context_window, minibatch=args.minibatch,
            seed=args.seed)[2],
        long_stream, block=args.block)
    report["paired_bootstrap_combined_vs_reference"] = paired_bootstrap(
        reference_predictions != reference_clean,
        combined_predictions != combined_clean,
        seed=args.seed)

    combined_accuracy = report["controls"]["combined"]["frozen_clean_accuracy"]
    low, high = report["controls"]["combined"]["frozen_clean_wilson_95"]
    if low > gate:
        decision = "passed"
    elif high < gate:
        decision = "failed"
    else:
        decision = "indeterminate"
    report["gate_decision"] = {
        "combined_frozen_clean_accuracy": combined_accuracy,
        "threshold": gate,
        "wilson_95": [low, high],
        "decision": decision,
        "next_step": {
            "passed": "Report M2 frozen accuracy, then may return to four phases.",
            "failed": "Move to v0.2 generator (common-component calibration + "
                      "acceptance criterion); retry gate there.",
            "indeterminate": "One seed insufficient; add seeds or widen eval "
                             "before any gate claim.",
        }[decision],
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(f"Gate threshold (clean): {gate:.4f}", flush=True)
    print(f"Combined clean: {combined_accuracy:.4f} "
          f"Wilson [{low:.4f}, {high:.4f}] -> {decision}", flush=True)
    print(f"Paired bootstrap (combined - reference errors): "
          f"{report['paired_bootstrap_combined_vs_reference']}", flush=True)
    print(f"Results: {args.output.resolve()}", flush=True)


if __name__ == "__main__":
    main()