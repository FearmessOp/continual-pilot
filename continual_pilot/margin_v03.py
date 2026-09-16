"""Margin diagnostic on reproduced students; halts if records fail to match.

Does NOT change the student, generator, acceptance criterion or gate formula.
Does NOT run v0.4. Reproduces the old combined student and the v0.3 primary
student deterministically, verifies mandatory matches against the stored
reports, persists final weights and per-example predictions, then reports raw
and scale-normalized teacher margins with error concentration by quintile.
"""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import torch

import diagnose
import diagnose_v02 as diagnostics
from pilot import Generator
from generator_v03 import GeneratorV03

CLASSES = 4
FIXED_MARGIN_THRESHOLDS = (0.1, 0.25, 0.5)  # Normalized; preregistered.
QUINTILES = 5
CONCENTRATION_TARGET = 0.70  # Lowest-quintile error share flag; not a test.


def digest_array(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def clean_scores(scorer, z, rule):
    """Full clean score matrix (offset included for v0.3) before argmax."""
    return scorer(z, rule)


def score_std(scorer, mixed_z, rule):
    """Population std over all sample and class elements of the clean scores."""
    scores = clean_scores(scorer, mixed_z, rule)
    return float(np.std(scores))


def mixed_calibration_z(generator, *, seed, per_mixture=10000):
    """Equal M1/M2 latent draw for scale calibration; independent stream."""
    rng = np.random.default_rng(seed)
    pieces = []
    for mixture in range(2):
        components = rng.choice(4, size=per_mixture, p=generator.weights[mixture])
        pieces.append(rng.normal(size=(per_mixture, 8))
                     + generator.means[components])
    return np.concatenate(pieces)


def v02_base_scores(generator, z, rule):
    """Pilot generator clean scores: alpha*common + specific, no offset."""
    common = generator.component(z[:, :2], 0)
    specific = generator.component(z[:, 2:4] if rule == 0 else z[:, 4:6],
                                   rule + 1)
    return generator.alpha * common + specific


def two_seed_stream(generator, first_count, first_seed, extra_count, extra_seed):
    """Reproduce the old combined training stream: two concatenated draws."""
    first = diagnose.single_regime(generator, first_count, first_seed)
    if extra_count <= 0:
        return first
    tail = diagnose.single_regime(generator, extra_count, extra_seed)
    return tuple(np.concatenate((first[i], tail[i])) for i in range(3))


def confusion_matrix(predictions, clean):
    matrix = np.zeros((CLASSES, CLASSES), dtype=np.int64)
    for true, pred in zip(clean, predictions):
        matrix[true, pred] += 1
    return matrix


def margin_report(scores, predictions, clean, *, scale):
    """Raw/normalized margins, fixed-threshold shares, quintile concentration."""
    ordered = np.sort(scores, axis=1)
    raw_margin = (ordered[:, -1] - ordered[:, -2]).astype(np.float64)
    normalized = raw_margin / scale
    errors = (predictions != clean).astype(np.int64)
    total_errors = int(errors.sum())

    threshold_shares = {
        f"below_{value}": float(np.mean(normalized < value))
        for value in FIXED_MARGIN_THRESHOLDS
    }
    raw_q = np.quantile(raw_margin, [0.1, 0.25, 0.5, 0.75, 0.9]).tolist()
    norm_q = np.quantile(normalized, [0.1, 0.25, 0.5, 0.75, 0.9]).tolist()

    order = np.argsort(raw_margin, kind="stable")
    bins = np.array_split(order, QUINTILES)
    quintiles = []
    for index, ids in enumerate(bins):
        bin_errors = int(errors[ids].sum())
        quintiles.append({
            "quintile": index + 1,
            "count": int(len(ids)),
            "raw_margin_min": float(raw_margin[ids].min()),
            "raw_margin_max": float(raw_margin[ids].max()),
            "error_count": bin_errors,
            "within_bin_error_rate": (bin_errors / len(ids)) if len(ids) else None,
            "share_of_total_errors": (bin_errors / total_errors)
                                     if total_errors else None,
        })
    lowest_share = quintiles[0]["share_of_total_errors"]
    return {
        "scale_std": scale,
        "raw_margin_quantiles_10_25_50_75_90": raw_q,
        "normalized_margin_quantiles_10_25_50_75_90": norm_q,
        "normalized_below_fixed_thresholds": threshold_shares,
        "total_errors": total_errors,
        "quintiles": quintiles,
        "lowest_quintile_error_share": lowest_share,
        "concentration_flag": (None if total_errors == 0
                               else lowest_share >= CONCENTRATION_TARGET),
        "concentration_target": CONCENTRATION_TARGET,
    }


def reproduce_v02(args, record_dir):
    """Old combined student: seed 7, two-seed 40k stream, mb 16, no context."""
    stored = json.loads(
        (Path(__file__).parent / "results_v02" / "summary.json").read_text(
            encoding="utf-8"))
    combined = stored["controls"]["combined"]
    generator = Generator(seed=7, alpha=0.5, noise=0.05)
    stream = two_seed_stream(generator, 10000, 107, 30000, 108)
    initial = diagnose.make_model(64, False, seed=7)
    initial_digest = diagnose.state_digest(initial)
    if initial_digest != combined["initial_state_sha256"]:
        raise AssertionError("v0.2 initial state mismatch; halting diagnostic")
    model, _, train_predictions, steps, _ = diagnose.train_online(
        initial, stream, lr=0.001, use_context=False, context_window=64,
        minibatch=16, seed=7)
    if steps != combined["optimizer_steps"]:
        raise AssertionError("v0.2 optimizer step mismatch; halting diagnostic")

    predictions, clean, noisy = diagnostics.frozen_evaluation(
        model, generator, use_context=False, context_window=64,
        seed=707, count=20000)
    accuracy = float(np.mean(predictions == clean))
    matrix = confusion_matrix(predictions, clean)
    stored_matrix = np.array(combined["confusion_matrix_true_by_pred"])
    if abs(accuracy - combined["frozen_clean_accuracy"]) > 1e-9:
        raise AssertionError("v0.2 clean accuracy mismatch; halting diagnostic")
    if not np.array_equal(matrix, stored_matrix):
        raise AssertionError("v0.2 confusion matrix mismatch; halting diagnostic")

    eval_z = reproduce_eval_latents(generator, seed=707 + 1, count=20000)
    scale = {rule: score_std(
        lambda z, r: v02_base_scores(generator, z, r),
        mixed_calibration_z(generator, seed=130000), rule)
        for rule in (0, 1)}
    scores = v02_base_scores(generator, eval_z, 0)
    if not np.array_equal(scores.argmax(axis=1), clean):
        raise AssertionError("v0.2 score argmax != clean targets; halting")
    if scale[0] <= 0 or not np.isfinite(scale[0]):
        raise AssertionError("v0.2 scale invalid; halting diagnostic")

    save_records(record_dir / "v02_combined", model, train_predictions,
                 predictions, clean, noisy)
    report = margin_report(scores, predictions, clean, scale=scale[0])
    report.update({
        "student": "old_combined",
        "generator": "pilot_seed7",
        "reproduced_clean_accuracy": accuracy,
        "matched_confusion_matrix": True,
        "matched_initial_state": True,
        "matched_optimizer_steps": True,
        "final_state_sha256": diagnose.state_digest(model),
        "prediction_sequence_equality_proven": False,
    })
    return report


def reproduce_eval_latents(generator, *, seed, count):
    """Recompute full-precision evaluation latents in prediction order."""
    warm = 64 * 4
    _ = diagnose.single_regime(generator, warm, seed - 1)  # Same draw as warmup.
    _, _, _, z = generator.sample(count, 0, 0, np.random.default_rng(seed))
    return z


def reproduce_v03(args, record_dir):
    """v0.3 primary student: generator seed 1000, gate protocol, seed-7 init."""
    stored = json.loads(
        (Path(__file__).parent / "results_gate_v03" / "summary.json").read_text(
            encoding="utf-8"))
    primary = stored["controls"]["64"]
    generator = GeneratorV03(seed=1000, alpha=0.5, noise=0.05,
                             calibration_count=20000)
    stream = diagnose.single_regime(generator, 40000, 120100)
    initial = diagnose.make_model(64, False, seed=7)
    if diagnose.state_digest(initial) != primary["initial_state_sha256"]:
        raise AssertionError("v0.3 initial state mismatch; halting diagnostic")
    model, _, train_predictions, steps, _ = diagnose.train_online(
        initial, stream, lr=0.001, use_context=False, context_window=64,
        minibatch=16, seed=7)
    if steps != primary["optimizer_steps"]:
        raise AssertionError("v0.3 optimizer step mismatch; halting diagnostic")

    predictions, clean, noisy = diagnostics.frozen_evaluation(
        model, generator, use_context=False, context_window=64,
        seed=120300, count=20000)
    accuracy = float(np.mean(predictions == clean))
    matrix = confusion_matrix(predictions, clean)
    stored_matrix = np.array(primary["evaluation"]["confusion_matrix_true_by_pred"])
    if abs(accuracy - primary["evaluation"]["frozen_clean_accuracy"]) > 1e-9:
        raise AssertionError("v0.3 clean accuracy mismatch; halting diagnostic")
    if not np.array_equal(matrix, stored_matrix):
        raise AssertionError("v0.3 confusion matrix mismatch; halting diagnostic")
    final_digest = diagnose.state_digest(model)
    if final_digest != primary["evaluation"]["model_state_sha256"]:
        raise AssertionError("v0.3 final state SHA mismatch; halting diagnostic")
    if digest_array(clean) != primary["evaluation"]["clean_targets_sha256"]:
        raise AssertionError("v0.3 clean target SHA mismatch; halting diagnostic")
    if digest_array(noisy) != primary["evaluation"]["noisy_targets_sha256"]:
        raise AssertionError("v0.3 noisy target SHA mismatch; halting diagnostic")

    eval_z = reproduce_eval_latents(generator, seed=120301, count=20000)
    scale = {rule: score_std(
        generator._base_scores_with_offset if hasattr(
            generator, "_base_scores_with_offset") else
        (lambda z, r: generator._base_scores(z, r) + generator.offsets[r]),
        mixed_calibration_z(generator, seed=130100), rule)
        for rule in (0, 1)}
    scores = generator._base_scores(eval_z, 0) + generator.offsets[0]
    if not np.array_equal(scores.argmax(axis=1), clean):
        raise AssertionError("v0.3 score argmax != clean targets; halting")
    if scale[0] <= 0 or not np.isfinite(scale[0]):
        raise AssertionError("v0.3 scale invalid; halting diagnostic")

    save_records(record_dir / "v03_primary", model, train_predictions,
                 predictions, clean, noisy)
    report = margin_report(scores, predictions, clean, scale=scale[0])
    report.update({
        "student": "v03_primary",
        "generator": "v03_seed1000",
        "reproduced_clean_accuracy": accuracy,
        "matched_confusion_matrix": True,
        "matched_initial_state": True,
        "matched_optimizer_steps": True,
        "matched_final_state_sha": True,
        "matched_target_shas": True,
        "final_state_sha256": final_digest,
        "prediction_sequence_equality_proven": True,
    })
    return report


def save_records(directory, model, train_predictions, eval_predictions,
                 clean, noisy):
    """Persist final weights and per-example predictions with integrity hashes."""
    directory.mkdir(parents=True, exist_ok=True)
    weights_path = directory / "final_weights.pt"
    torch.save(model.state_dict(), weights_path)
    arrays = {
        "train_predictions": np.asarray(train_predictions, dtype=np.int64),
        "eval_predictions": np.asarray(eval_predictions, dtype=np.int64),
        "eval_clean": np.asarray(clean, dtype=np.int64),
        "eval_noisy": np.asarray(noisy, dtype=np.int64),
    }
    np.savez(directory / "predictions.npz", **arrays)
    manifest = {
        "final_state_sha256": diagnose.state_digest(model),
        "weights_file_sha256": hashlib.sha256(
            weights_path.read_bytes()).hexdigest(),
        "arrays": {name: {"count": int(value.size),
                          "sha256": digest_array(value)}
                   for name, value in arrays.items()},
    }
    (directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    # Verify the records load back and match before proceeding.
    with np.load(directory / "predictions.npz") as loaded:
        for name, value in arrays.items():
            if digest_array(loaded[name]) != manifest["arrays"][name]["sha256"]:
                raise AssertionError(f"Record load mismatch for {name}; halting")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "results_margin_v03")
    args = parser.parse_args()
    output = args.output / "summary.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    record_dir = args.output / "records"

    old_report = reproduce_v02(args, record_dir)
    new_report = reproduce_v03(args, record_dir)

    report = {
        "revision": "margin-diagnostic-v03",
        "scope": "Reproduce old combined and v0.3 primary; margin diagnostic only.",
        "fixed_margin_thresholds": list(FIXED_MARGIN_THRESHOLDS),
        "quintiles": QUINTILES,
        "concentration_target": CONCENTRATION_TARGET,
        "scale_calibration": {
            "distribution": "equal M1/M2 mixture, 10000 per mixture",
            "old_seed": 130000, "v03_seed": 130100,
            "definition": "population std over all sample and class score elements",
        },
        "limitations": [
            "No student, generator, acceptance or gate-formula change; no v0.4.",
            "Score margin is not a direct geometric distance to the boundary.",
            "Old-generator prediction sequence equality is NOT proven.",
            "Quintile concentration is a descriptive flag, not a hypothesis test.",
            "Teacher seed and calibration also changed; old-new gap is not the "
            "isolated causal effect of the offset.",
        ],
        "old_combined": old_report,
        "v03_primary": new_report,
        "environment": {"python": platform.python_version(),
                        "numpy": np.__version__, "torch": torch.__version__,
                        "device": "cpu"},
    }
    args.output.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    for label, section in (("old", old_report), ("v03", new_report)):
        print(f"{label}: errors={section['total_errors']}, "
              f"lowest-quintile share="
              f"{section['lowest_quintile_error_share']}, "
              f"flag={section['concentration_flag']}, "
              f"below0.1={section['normalized_below_fixed_thresholds']['below_0.1']:.4f}",
              flush=True)
    print(f"Results: {output.resolve()}", flush=True)


if __name__ == "__main__":
    main()