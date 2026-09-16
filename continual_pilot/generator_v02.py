"""v0.2 generator with common-component calibration and deterministic acceptance.

Does NOT modify pilot.py, diagnose.py, diagnose_v02.py, or rerun any experiment.
This module only builds and accepts a generator per the preregistered spec, then
reports the acceptance record and probes. The gate itself is a later step.

Key preregistered fixes versus the pilot generator:
  1. The common component is calibrated on the REAL mixed z distribution
     (equal parts M1 and M2), not on a standard normal. The pilot's teacher
     scale used N(0,1) samples, mismatching the (+/-1, +/-1) mean mixture that
     actually feeds the common component (z[:, :2]).
  2. Acceptance is deterministic: seeds are tried in a fixed order, the first
     acceptable seed is taken, tried/rejected counts are reported, and a 200
     attempt cap fails the design (the criterion is never loosened).
  3. The balance criterion (each class 18%-35%), applied under R1 and R2 and
     under M1 and M2, and the disagreement band (40%-70%), must ALL hold on the
     same seed. This band nominally locks the gate to 92.5%-93.5% clean.

Single seed per accepted generator; exploratory; not a significance test.
"""
import argparse
import json
import platform
from pathlib import Path

import numpy as np
import torch

import diagnose

CLASSES = 4
CLASS_LOW = 0.18            # Preregistered lower bound on every class fraction.
CLASS_HIGH = 0.35           # Preregistered upper bound on every class fraction.
DISAGREEMENT_LOW = 0.40     # Preregistered lower bound on R1/R2 disagreement.
DISAGREEMENT_HIGH = 0.70    # Preregistered upper bound on R1/R2 disagreement.
MAX_ATTEMPTS = 200          # Preregistered cap; exceeding it fails the design.


class GeneratorV02:
    """Same structure as the pilot generator, but the common component is

    calibrated on the real mixed-z distribution rather than N(0, 1). All other
    mechanics (orthonormal projection, additive common/specific teachers,
    symmetric label noise) are identical so results stay comparable.
    """

    def __init__(self, seed=7, alpha=0.5, noise=0.05, calibration_count=20000):
        self.alpha, self.noise = alpha, noise
        rng = np.random.default_rng(seed)
        self.w = np.linalg.qr(rng.normal(size=(32, 8)))[0]
        self.means = np.zeros((4, 8))
        self.means[:, :2] = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
        self.weights = (np.array([.4, .3, .2, .1]),
                        np.array([.1, .2, .3, .4]))
        # Teacher weight matrices are drawn exactly like the pilot for parity.
        raw_teachers = []
        for _ in range(3):
            a = rng.normal(size=(2, 16))
            b = rng.normal(size=(16, 4)) / 4
            raw_teachers.append((a, b))
        # Calibrate each teacher's scale on the z-columns it actually consumes,
        # sampled from the real mixture (equal parts M1 and M2). The common
        # teacher (index 0) reads z[:, :2], whose real distribution is a Gaussian
        # mixture with means (+/-1, +/-1) - NOT N(0, 1).
        column_for = {0: (0, 2), 1: (2, 4), 2: (4, 6)}
        self.teachers = []
        for index, (a, b) in enumerate(raw_teachers):
            start, stop = column_for[index]
            z = self._mixed_z(rng, calibration_count)[:, start:stop]
            raw = np.tanh(z @ a) @ b
            centered = raw - raw.mean(axis=1, keepdims=True)
            self.teachers.append((a, b, float(centered.std())))

    def _mixed_z(self, rng, count):
        """Latent factors drawn equally from M1 and M2 component weights."""
        half = count // 2
        pieces = []
        for mixture, size in ((0, half), (1, count - half)):
            components = rng.choice(4, size=size, p=self.weights[mixture])
            pieces.append(rng.normal(size=(size, 8)) + self.means[components])
        return np.concatenate(pieces)

    def component(self, z, index):
        a, b, scale = self.teachers[index]
        raw = np.tanh(z @ a) @ b
        return (raw - raw.mean(axis=1, keepdims=True)) / scale

    def labels(self, z, rule):
        common = self.component(z[:, :2], 0)
        specific = self.component(z[:, 2:4] if rule == 0 else z[:, 4:6],
                                  rule + 1)
        return (self.alpha * common + specific).argmax(axis=1)

    def sample(self, count, mixture, rule, rng):
        components = rng.choice(4, size=count, p=self.weights[mixture])
        z = rng.normal(size=(count, 8)) + self.means[components]
        clean = self.labels(z, rule)
        flip = rng.random(count) < self.noise
        offsets = rng.integers(1, 4, size=count)
        noisy = np.where(flip, (clean + offsets) % 4, clean)
        return (z @ self.w.T).astype(np.float32), noisy, clean, z


def acceptance_metrics(generator, *, seed, count=20000):
    """Class fractions under R1 and R2 x M1 and M2, plus disagreement per mixture.

    Uses a stream seed independent of training/calibration/evaluation streams.
    """
    rng = np.random.default_rng(seed)
    fractions = {}
    disagreement = {}
    min_fraction = 1.0
    for mixture in range(2):
        _, _, _, z = generator.sample(count, mixture, 0, rng)
        r1 = generator.labels(z, 0)
        r2 = generator.labels(z, 1)
        for rule, labels in ((1, r1), (2, r2)):
            frac = (np.bincount(labels, minlength=CLASSES) / count)
            fractions[f"M{mixture + 1}_R{rule}"] = frac.tolist()
            min_fraction = min(min_fraction, float(frac.min()))
        disagreement[f"M{mixture + 1}"] = float(np.mean(r1 != r2))
    return {
        "class_fractions": fractions,
        "disagreement": disagreement,
        "min_class_fraction": min_fraction,
        "max_class_fraction": max(max(f) for f in fractions.values()),
    }


def is_acceptable(metrics):
    """All class fractions in [LOW, HIGH]; all disagreements in the band."""
    fractions_ok = all(CLASS_LOW <= value <= CLASS_HIGH
                       for frac in metrics["class_fractions"].values()
                       for value in frac)
    disagreement_ok = all(DISAGREEMENT_LOW <= d <= DISAGREEMENT_HIGH
                          for d in metrics["disagreement"].values())
    return bool(fractions_ok and disagreement_ok)


def accept_generator(*, alpha, noise, seed_start, metric_seed, calibration_count):
    """Try seeds in fixed order; take the first acceptable; report the record.

    Never loosens the criterion. Exceeding MAX_ATTEMPTS is a design failure.
    """
    rejected = []
    for attempt in range(MAX_ATTEMPTS):
        seed = seed_start + attempt
        generator = GeneratorV02(seed=seed, alpha=alpha, noise=noise,
                                 calibration_count=calibration_count)
        metrics = acceptance_metrics(generator, seed=metric_seed + attempt,
                                     count=calibration_count)
        if is_acceptable(metrics):
            return {
                "accepted": True,
                "accepted_seed": seed,
                "attempts_tried": attempt + 1,
                "rejected_count": len(rejected),
                "rejected_seeds": rejected,
                "accepted_metrics": metrics,
            }, generator
        rejected.append({"seed": seed,
                         "min_class_fraction": metrics["min_class_fraction"],
                         "max_class_fraction": metrics["max_class_fraction"],
                         "disagreement": metrics["disagreement"]})
    return {
        "accepted": False,
        "attempts_tried": MAX_ATTEMPTS,
        "rejected_count": len(rejected),
        "rejected_seeds": rejected,
        "note": "Design failure: no seed satisfied the criterion; version must "
                "change and the criterion must NOT be loosened.",
    }, None


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--noise", type=float, default=0.05)
    parser.add_argument("--seed-start", type=int, default=1000)
    parser.add_argument("--metric-seed", type=int, default=50000)
    parser.add_argument("--probe-window", type=int, default=64)
    parser.add_argument("--calibration-count", type=int, default=20000)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "results_generator_v02")
    args = parser.parse_args()
    for name in ("probe_window", "calibration_count", "threads"):
        if getattr(args, name) < 1:
            parser.error(f"{name} must be positive")
    if not (0 <= args.noise < 0.75) or args.alpha < 0:
        parser.error("Require 0 <= noise < .75 and alpha >= 0")
    return args


def main():
    args = parse_args()
    torch.set_num_threads(args.threads)
    torch.use_deterministic_algorithms(True)

    record, generator = accept_generator(
        alpha=args.alpha, noise=args.noise, seed_start=args.seed_start,
        metric_seed=args.metric_seed, calibration_count=args.calibration_count)

    report = {
        "revision": "generator-v02",
        "config": {key: str(value) if isinstance(value, Path) else value
                   for key, value in vars(args).items()},
        "environment": {"python": platform.python_version(),
                        "torch": torch.__version__, "numpy": np.__version__,
                        "device": "cpu"},
        "criterion": {
            "class_fraction_band": [CLASS_LOW, CLASS_HIGH],
            "applies_to": "each class, under R1 and R2, under M1 and M2",
            "disagreement_band": [DISAGREEMENT_LOW, DISAGREEMENT_HIGH],
            "max_attempts": MAX_ATTEMPTS,
            "nominal_gate_band": [0.925, 0.935],
            "note": "Common component calibrated on the real mixed-z "
                    "distribution (equal M1/M2), not N(0,1). Nominal gate band "
                    "follows from the class-fraction band; the realized gate is "
                    "computed later from an independent calibration stream.",
        },
        "acceptance": record,
    }

    if generator is not None:
        # Prob is a generator diagnostic (spec order: accept -> prob -> student
        # -> gate). It does NOT fix the student or run the gate here.
        report["summary_probe_full_noisy"] = _probe(
            generator, window=args.probe_window, seed=args.metric_seed + 500,
            use_4freq_only=False)
        report["summary_probe_4freq_noisy"] = _probe(
            generator, window=args.probe_window, seed=args.metric_seed + 600,
            use_4freq_only=True)

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    if generator is None:
        print(f"Design FAILED after {MAX_ATTEMPTS} attempts; version must change.",
              flush=True)
    else:
        acc = record
        print(f"Accepted seed {acc['accepted_seed']} after {acc['attempts_tried']} "
              f"attempts ({acc['rejected_count']} rejected).", flush=True)
        print(f"min class fraction {acc['accepted_metrics']['min_class_fraction']:.4f}, "
              f"max {acc['accepted_metrics']['max_class_fraction']:.4f}", flush=True)
        print(f"disagreement {acc['accepted_metrics']['disagreement']}", flush=True)
        print(f"4-freq probe {report['summary_probe_4freq_noisy']['regime_probe_test_accuracy']:.4f}; "
              f"full probe {report['summary_probe_full_noisy']['regime_probe_test_accuracy']:.4f}",
              flush=True)
    print(f"Results: {args.output.resolve()}", flush=True)


def _probe(generator, *, window, seed, use_4freq_only):
    """Noisy-label regime probe on the accepted v0.2 generator; overlap noted."""
    from pilot import Context

    def build(rule, stream_seed):
        rng = np.random.default_rng(stream_seed)
        x, noisy, _, _ = generator.sample(window * 8, 1, rule, rng)
        context = Context(window)
        rows = []
        for i in range(len(noisy)):
            if i >= window:
                summary = context.encode(x[i])[32:]
                rows.append(summary[:CLASSES] if use_4freq_only else summary)
            context.observe(x[i], noisy[i])
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
        "effective_independent_blocks_estimate": int(2 * len(test[0]) // window),
        "note": "Windows overlap; raw rows overstate independence. Noisy labels "
                "match the student. Re-measured on the v0.2 generator; the pilot "
                "probe result is NOT carried over.",
    }


if __name__ == "__main__":
    main()