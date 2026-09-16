"""v0.3 generator: build class balance via per-class additive offsets.

Does NOT modify pilot.py, diagnose.py, diagnose_v02.py, generator_v02.py, or
rerun any experiment. Only builds and accepts a generator per the preregistered
v0.3 spec, then reports the acceptance record and probes (probes only if
accepted). The gate itself is a later step.

Why v0.3 exists (spec fix, not a generator fix): v0.2 left balance to rejection
sampling. The criterion is 16 simultaneous narrow-band conditions (4 classes x
R1/R2 x M1/M2). Random tanh teachers segment the space unevenly via argmax, so
the joint probability of all 16 holding is effectively zero; rejection sampling
never finds it. Balance must be BUILT, not searched. v0.3 builds it with
per-class additive offsets and keeps rejection sampling only as verification.

Construction:
  s_r(z) = alpha * h_common(z1, z2) + h_specific(z_r) + beta_r,  beta_r in R^4.
The offset beta_r is calibrated on an independent equal M1/M2 mixture to pull the
class marginals toward 1/4 via fixed iterative log-ratio correction
(beta <- beta + eta * log(target / observed)), fixed iterations and eta. The
common/specific structure is preserved (offset is an additive constant; it does
NOT touch the shared subfunction). The task is not made easier: decision
boundaries shift, but class count and teacher sharpness are unchanged.

IMPORTANT identifiability note: the offset targets the MIXED marginal (equal
M1/M2), whereas acceptance measures each class under R1 and R2, under M1 and M2
separately. So the offset only corrects the mixed expectation; under the M1 and
M2 breakdowns the shares deviate in opposite directions. That deviation is
exactly why the 18%-35% band has slack, and if it exceeds the band the seed is
still rejected. The offset does NOT guarantee balance; it only centers the
mixed expectation at 1/4.

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
OFFSET_ITERATIONS = 50      # Fixed; preregistered.
OFFSET_ETA = 0.5            # Fixed; preregistered.
OFFSET_TARGET = 0.25        # Each class equal in the calibration mixture.
OFFSET_CALIBRATION_COUNT = 20000  # Fixed; preregistered.
MECHANICAL_TOLERANCE = 0.02  # +/- 2% mixed-marginal check (verification only).


class GeneratorV03:
    """v0.2 mechanics plus a per-rule additive class offset that builds balance.

    The common component is calibrated on the real mixed-z distribution (as in
    v0.2). On top of that, each rule gets an offset beta_r found by fixed
    iterative log-ratio correction on an independent equal M1/M2 mixture.
    """

    def __init__(self, seed=7, alpha=0.5, noise=0.05,
                 calibration_count=20000, offset_seed=None):
        self.alpha, self.noise = alpha, noise
        rng = np.random.default_rng(seed)
        self.w = np.linalg.qr(rng.normal(size=(32, 8)))[0]
        self.means = np.zeros((4, 8))
        self.means[:, :2] = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
        self.weights = (np.array([.4, .3, .2, .1]),
                        np.array([.1, .2, .3, .4]))
        raw_teachers = []
        for _ in range(3):
            a = rng.normal(size=(2, 16))
            b = rng.normal(size=(16, 4)) / 4
            raw_teachers.append((a, b))
        # Common component (index 0) calibrated on the real mixed-z, as in v0.2.
        column_for = {0: (0, 2), 1: (2, 4), 2: (4, 6)}
        self.teachers = []
        for index, (a, b) in enumerate(raw_teachers):
            start, stop = column_for[index]
            z = self._mixed_z(rng, calibration_count)[:, start:stop]
            raw = np.tanh(z @ a) @ b
            centered = raw - raw.mean(axis=1, keepdims=True)
            self.teachers.append((a, b, float(centered.std())))
        # Offsets are teacher-dependent, so they are recomputed per generator.
        # A dedicated offset RNG stream, independent of acceptance/train/eval.
        self.offset_seed = seed + 90000 if offset_seed is None else offset_seed
        self.offsets = self._calibrate_offsets(OFFSET_CALIBRATION_COUNT)

    def _mixed_z(self, rng, count):
        """Latent factors drawn equally from M1 and M2 component weights."""
        half = count // 2
        pieces = []
        for mixture, size in ((0, half), (1, count - half)):
            components = rng.choice(4, size=size, p=self.weights[mixture])
            pieces.append(rng.normal(size=(size, 8)) + self.means[components])
        return np.concatenate(pieces)

    def _base_scores(self, z, rule):
        """Additive common + specific scores BEFORE the class offset."""
        common = self.component(z[:, :2], 0)
        specific = self.component(z[:, 2:4] if rule == 0 else z[:, 4:6],
                                  rule + 1)
        return self.alpha * common + specific

    def _calibrate_offsets(self, count):
        """Fixed iterative log-ratio offsets pulling mixed marginals to 1/4.

        Deterministic given the generator seed; uses its own RNG stream so it
        never consumes acceptance, training or evaluation randomness.
        """
        rng = np.random.default_rng(self.offset_seed)
        z = self._mixed_z(rng, count)
        offsets = {}
        for rule in (0, 1):
            base = self._base_scores(z, rule)
            beta = np.zeros(CLASSES)
            for _ in range(OFFSET_ITERATIONS):
                labels = (base + beta).argmax(axis=1)
                observed = np.bincount(labels, minlength=CLASSES) / count
                # Guard against empty classes: floor keeps the log finite and
                # still pushes an empty class strongly upward.
                safe = np.maximum(observed, 1.0 / count)
                beta = beta + OFFSET_ETA * np.log(OFFSET_TARGET / safe)
            offsets[rule] = beta
        return offsets

    def component(self, z, index):
        a, b, scale = self.teachers[index]
        raw = np.tanh(z @ a) @ b
        return (raw - raw.mean(axis=1, keepdims=True)) / scale

    def labels(self, z, rule):
        return (self._base_scores(z, rule) + self.offsets[rule]).argmax(axis=1)

    def sample(self, count, mixture, rule, rng):
        components = rng.choice(4, size=count, p=self.weights[mixture])
        z = rng.normal(size=(count, 8)) + self.means[components]
        clean = self.labels(z, rule)
        flip = rng.random(count) < self.noise
        offsets = rng.integers(1, 4, size=count)
        noisy = np.where(flip, (clean + offsets) % 4, clean)
        return (z @ self.w.T).astype(np.float32), noisy, clean, z

    def mixed_marginal_fractions(self, *, seed, count):
        """Class fractions on an equal M1/M2 mixture per rule (mechanical check).

        This measures what the offset directly targets, on an INDEPENDENT
        stream. It is verification, NOT acceptance; acceptance uses the 16
        R1/R2 x M1/M2 conditions below.
        """
        rng = np.random.default_rng(seed)
        z = self._mixed_z(rng, count)
        result = {}
        for rule in (0, 1):
            labels = self.labels(z, rule)
            result[f"R{rule + 1}"] = (
                np.bincount(labels, minlength=CLASSES) / count).tolist()
        return result


def acceptance_metrics(generator, *, seed, count=20000):
    """Class fractions under R1 and R2 x M1 and M2, plus disagreement per mixture.

    Uses a stream seed independent of calibration/offset/training/evaluation.
    """
    rng = np.random.default_rng(seed)
    fractions = {}
    disagreement = {}
    min_fraction = 1.0
    max_fraction = 0.0
    for mixture in range(2):
        _, _, _, z = generator.sample(count, mixture, 0, rng)
        r1 = generator.labels(z, 0)
        r2 = generator.labels(z, 1)
        for rule, labels in ((1, r1), (2, r2)):
            frac = np.bincount(labels, minlength=CLASSES) / count
            fractions[f"M{mixture + 1}_R{rule}"] = frac.tolist()
            min_fraction = min(min_fraction, float(frac.min()))
            max_fraction = max(max_fraction, float(frac.max()))
        disagreement[f"M{mixture + 1}"] = float(np.mean(r1 != r2))
    return {
        "class_fractions": fractions,
        "disagreement": disagreement,
        "min_class_fraction": min_fraction,
        "max_class_fraction": max_fraction,
    }


def failure_reason(metrics):
    """Which criterion a rejected seed violates: 'balance', 'disagreement', both."""
    balance_ok = all(CLASS_LOW <= value <= CLASS_HIGH
                     for frac in metrics["class_fractions"].values()
                     for value in frac)
    disagreement_ok = all(DISAGREEMENT_LOW <= d <= DISAGREEMENT_HIGH
                          for d in metrics["disagreement"].values())
    reasons = []
    if not balance_ok:
        reasons.append("balance")
    if not disagreement_ok:
        reasons.append("disagreement")
    return reasons


def is_acceptable(metrics):
    return len(failure_reason(metrics)) == 0


def accept_generator(*, alpha, noise, seed_start, metric_seed, calibration_count):
    """Try seeds in fixed order; take the first acceptable; report the record.

    The offset is rebuilt for every candidate (teacher-dependent), then the
    unchanged acceptance procedure runs on top. Never loosens the criterion.
    Rejections are counted separately by reason.
    """
    rejected = []
    rejected_by = {"balance_only": 0, "disagreement_only": 0, "both": 0}
    for attempt in range(MAX_ATTEMPTS):
        seed = seed_start + attempt
        generator = GeneratorV03(seed=seed, alpha=alpha, noise=noise,
                                 calibration_count=calibration_count)
        metrics = acceptance_metrics(generator, seed=metric_seed + attempt,
                                     count=calibration_count)
        reasons = failure_reason(metrics)
        if not reasons:
            mixed = generator.mixed_marginal_fractions(
                seed=metric_seed + 40000 + attempt, count=calibration_count)
            return {
                "accepted": True,
                "accepted_seed": seed,
                "attempts_tried": attempt + 1,
                "rejected_count": len(rejected),
                "rejected_by_reason": rejected_by,
                "rejected_seeds": rejected,
                "accepted_metrics": metrics,
                "accepted_mixed_marginals": mixed,
            }, generator
        if reasons == ["balance"]:
            rejected_by["balance_only"] += 1
        elif reasons == ["disagreement"]:
            rejected_by["disagreement_only"] += 1
        else:
            rejected_by["both"] += 1
        rejected.append({"seed": seed, "reasons": reasons,
                         "min_class_fraction": metrics["min_class_fraction"],
                         "max_class_fraction": metrics["max_class_fraction"],
                         "disagreement": metrics["disagreement"]})
    return {
        "accepted": False,
        "attempts_tried": MAX_ATTEMPTS,
        "rejected_count": len(rejected),
        "rejected_by_reason": rejected_by,
        "rejected_seeds": rejected,
        "decision_tree": {
            "rejected_for_disagreement": "If failures are disagreement-driven, "
                "revisit alpha or teacher scale in v0.4.",
            "rejected_for_balance": "If failures are balance-driven, the offset "
                "method is insufficient; the decision rule (argmax) must change.",
        },
        "note": "Design failure: no seed satisfied the criterion; version must "
                "change and the criterion must NOT be loosened.",
    }, None


def probe(generator, *, window, seed, use_4freq_only):
    """Noisy-label regime probe on the accepted v0.3 generator; overlap noted."""
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
    model = diagnose.logistic_probe(train_x, train_y, seed=seed)
    with torch.no_grad():
        prediction = model(torch.from_numpy(test_x)).argmax(dim=1).numpy()
    return {
        "feature_dimension": int(train_x.shape[1]),
        "regime_probe_test_accuracy": float(np.mean(prediction == test_y)),
        "chance_level": 0.5,
        "raw_test_rows": int(len(test_y)),
        "distinct_windows_per_stream": int(len(test[0])),
        "effective_independent_blocks_estimate": int(2 * len(test[0]) // window),
        "note": "Windows overlap; raw rows overstate independence. Noisy labels "
                "match the student. Re-measured on the v0.3 generator.",
    }


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
                        default=Path(__file__).parent / "results_generator_v03")
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
        "revision": "generator-v03",
        "config": {key: str(value) if isinstance(value, Path) else value
                   for key, value in vars(args).items()},
        "environment": {"python": platform.python_version(),
                        "torch": torch.__version__, "numpy": np.__version__,
                        "device": "cpu"},
        "rationale": (
            "v0.2 left balance to rejection sampling over 16 simultaneous "
            "narrow-band conditions; the joint probability is effectively zero, "
            "so it was a specification error, not a generator failure. v0.3 "
            "BUILDS balance with per-class additive offsets and keeps rejection "
            "sampling only as verification."),
        "offset_spec": {
            "form": "s_r(z) = alpha*h_common + h_specific(z_r) + beta_r",
            "target": OFFSET_TARGET,
            "iterations": OFFSET_ITERATIONS,
            "eta": OFFSET_ETA,
            "calibration_count": OFFSET_CALIBRATION_COUNT,
            "calibration_distribution": "equal M1/M2 mixture",
            "recomputed_per_seed": True,
            "note": "Offset targets the MIXED marginal; acceptance measures the "
                    "R1/R2 x M1/M2 breakdown. The offset does not guarantee "
                    "balance, only centers the mixed expectation at 1/4.",
        },
        "criterion": {
            "class_fraction_band": [CLASS_LOW, CLASS_HIGH],
            "applies_to": "each class, under R1 and R2, under M1 and M2",
            "disagreement_band": [DISAGREEMENT_LOW, DISAGREEMENT_HIGH],
            "max_attempts": MAX_ATTEMPTS,
            "nominal_gate_band": [0.925, 0.935],
            "note": "Unchanged from v0.2. Realized gate computed later from an "
                    "independent calibration stream.",
        },
        "mechanical_tolerance": MECHANICAL_TOLERANCE,
        "acceptance": record,
    }

    if generator is not None:
        report["summary_probe_full_noisy"] = probe(
            generator, window=args.probe_window, seed=args.metric_seed + 500,
            use_4freq_only=False)
        report["summary_probe_4freq_noisy"] = probe(
            generator, window=args.probe_window, seed=args.metric_seed + 600,
            use_4freq_only=True)

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    if generator is None:
        by = record["rejected_by_reason"]
        print(f"Design FAILED after {MAX_ATTEMPTS} attempts.", flush=True)
        print(f"Rejections by reason: {by}", flush=True)
    else:
        acc = record
        print(f"Accepted seed {acc['accepted_seed']} after "
              f"{acc['attempts_tried']} attempts "
              f"({acc['rejected_count']} rejected, "
              f"{acc['rejected_by_reason']}).", flush=True)
        print(f"min class fraction "
              f"{acc['accepted_metrics']['min_class_fraction']:.4f}, "
              f"max {acc['accepted_metrics']['max_class_fraction']:.4f}",
              flush=True)
        print(f"disagreement {acc['accepted_metrics']['disagreement']}",
              flush=True)
        print(f"4-freq probe "
              f"{report['summary_probe_4freq_noisy']['regime_probe_test_accuracy']:.4f}; "
              f"full probe "
              f"{report['summary_probe_full_noisy']['regime_probe_test_accuracy']:.4f}",
              flush=True)
    print(f"Results: {args.output.resolve()}", flush=True)


if __name__ == "__main__":
    main()