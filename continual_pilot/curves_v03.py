"""Phase-3 forgetting/adaptation curves from stored Line 1 records; no retraining.

EXPLORATION on the ungated student: extracts, from saved predictions, how fast
A forgets R1 and how fast replay adapts to R2 across phase 3, in 1000-example
blocks. Halts if stored prediction hashes or reproduced phase regrets do not
match the impact report. Reproduces the four-phase stream (inputs are NOT stored)
with the same generator and seeds; stream-input bit-equality is NOT proven, only
phase-regret agreement against the impact summary. Does not run Line 2 or retrain.
"""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import torch

from generator_v03 import GeneratorV03
import impact_v03 as impact

BLOCK = 1000
PHASE = impact.PROTOCOL["phase_length"]
PHASE3_START = 2 * PHASE
PHASE3_STOP = 3 * PHASE
DAMAGE_LOW = 0.20   # Candidate window: phase-2 reference minus this drop.
DAMAGE_HIGH = 0.40  # Preregistered band edges; not selected from results.


def digest_array(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def load_predictions(records, method, seed):
    manifest = json.loads(
        (records / f"{method}_seed{seed}_manifest.json").read_text(
            encoding="utf-8"))
    npz_path = records / manifest["predictions_file"]
    with np.load(npz_path) as data:
        online = data["online_predictions"].copy()
    if digest_array(online) != manifest["online_predictions_sha256"]:
        raise AssertionError(f"{method} seed {seed} prediction hash mismatch")
    return online


def reproduce_phase3(generator, seed):
    """Reproduce the phase-3 slice: R2/M2 inputs, R1 and R2 clean labels."""
    rng = np.random.default_rng(seed)
    slices = {}
    for index, (mixture, rule) in enumerate(impact.PROTOCOL["schedule"]):
        x, noisy, clean, z = generator.sample(PHASE, mixture, rule, rng)
        if index == 2:  # Phase 3 is R2/M2; keep its latents to derive R1 labels.
            r1_labels = generator.labels(z, 0)  # Same inputs, rule R1.
            r2_labels = clean                    # Phase-3 clean labels are R2.
            slices = {"x": x, "noisy": noisy, "r1": r1_labels, "r2": r2_labels}
    return slices


def phase_regret_from_predictions(online, generator, seed):
    """Recompute per-phase oracle regret to match the impact report."""
    rng = np.random.default_rng(seed)
    parts = []
    for mixture, rule in impact.PROTOCOL["schedule"]:
        x, noisy, clean, _ = generator.sample(PHASE, mixture, rule, rng)
        parts.append((noisy, clean))
    noisy = np.concatenate([p[0] for p in parts])
    clean = np.concatenate([p[1] for p in parts])
    error = (online != noisy).astype(np.int64)
    oracle = (clean != noisy).astype(np.int64)
    regret = error - oracle
    result = []
    for phase in range(4):
        start = phase * PHASE
        result.append({
            "phase": phase + 1,
            "first_1000_regret": int(regret[start:start + 1000].sum()),
            "total_regret": int(regret[start:start + PHASE].sum()),
        })
    return result


def block_curves(online, phase3):
    """1000-block accuracies over phase 3: A's R1, replay's R2, and overlaps."""
    slice3 = online[PHASE3_START:PHASE3_STOP]
    r1, r2 = phase3["r1"], phase3["r2"]
    teacher_agreement = float(np.mean(r1 == r2))
    rows = []
    for start in range(0, PHASE, BLOCK):
        stop = start + BLOCK
        block_pred = slice3[start:stop]
        rows.append({
            "block_end": stop,
            "count": stop - start,
            "pred_vs_R1_accuracy": float(np.mean(block_pred == r1[start:stop])),
            "pred_vs_R2_accuracy": float(np.mean(block_pred == r2[start:stop])),
        })
    return rows, teacher_agreement


def candidate_window(curve, phase2_reference):
    """Blocks where A's R1 accuracy sits DAMAGE_LOW..DAMAGE_HIGH below phase 2.

    Reports candidate phase-length ranges only; online block accuracies are NOT
    frozen-checkpoint measurements. Any range here is validated in a separate
    pilot before entering a preregistration.
    """
    low = phase2_reference - DAMAGE_HIGH   # Larger drop = lower accuracy bound.
    high = phase2_reference - DAMAGE_LOW
    hits = [row["block_end"] for row in curve
            if low <= row["pred_vs_R1_accuracy"] <= high]
    return {
        "phase2_reference_accuracy": phase2_reference,
        "damage_band": [DAMAGE_LOW, DAMAGE_HIGH],
        "r1_accuracy_band": [low, high],
        "blocks_in_band_by_example_index": hits,
        "note": "Online blocks, not frozen checkpoints; candidate ranges only.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "results_curves_v03")
    args = parser.parse_args()
    output = args.output / "summary.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    generator = GeneratorV03(
        seed=impact.PROTOCOL["generator_seed"], alpha=impact.PROTOCOL["alpha"],
        noise=impact.PROTOCOL["noise"],
        calibration_count=impact.PROTOCOL["generator_calibration_count"])
    records = Path(__file__).parent / "results_impact_v03" / "records"
    impact_summary = json.loads(
        (Path(__file__).parent / "results_impact_v03"
         / "summary.json").read_text(encoding="utf-8"))

    report = {
        "revision": "line1-curves-v03",
        "label": impact.LABEL,
        "scope": "Phase-3 curves from stored records; no retraining, no Line 2.",
        "block": BLOCK,
        "damage_band": [DAMAGE_LOW, DAMAGE_HIGH],
        "seeds": {},
        "limitations": [
            impact.LABEL,
            "Stream inputs were not stored; reproduced by seed. Input bit-"
            "equality is NOT proven, only phase-regret agreement.",
            "Online block accuracies are not frozen-checkpoint measurements.",
            "Candidate phase-length ranges must be validated in a separate pilot.",
            "Buffer R1 fraction in phase 3 is time-varying (~100% -> ~66.7%), "
            "not a constant two-thirds; conflicting-label reading is a strong "
            "candidate, not a proven mechanism.",
        ],
    }

    for seed in impact.PROTOCOL["training_seeds"]:
        phase3 = reproduce_phase3(generator, seed)
        seed_entry = {}
        for method in ("A", "replay"):
            online = load_predictions(records, method, seed)
            # Halt unless reproduced phase regret matches the stored report.
            reproduced = phase_regret_from_predictions(online, generator, seed)
            stored = impact_summary["seeds"][str(seed)][method]["phase_regret"]
            if reproduced != stored:
                raise AssertionError(
                    f"{method} seed {seed} phase-regret mismatch; halting")
            curve, agreement = block_curves(online, phase3)
            phase2_ref = impact_summary["seeds"][str(seed)][method][
                "frozen_m2r1_accuracy"]["2"]
            seed_entry[method] = {
                "teacher_R1_R2_agreement": agreement,
                "phase3_blocks": curve,
                "candidate_window_from_A_R1": (
                    candidate_window(curve, phase2_ref)
                    if method == "A" else None),
            }
        report["seeds"][str(seed)] = seed_entry
        a_first = seed_entry["A"]["phase3_blocks"][0]["pred_vs_R1_accuracy"]
        a_last = seed_entry["A"]["phase3_blocks"][-1]["pred_vs_R1_accuracy"]
        r_first = seed_entry["replay"]["phase3_blocks"][0]["pred_vs_R2_accuracy"]
        r_last = seed_entry["replay"]["phase3_blocks"][-1]["pred_vs_R2_accuracy"]
        print(f"seed={seed}: A R1 {a_first:.3f}->{a_last:.3f}; "
              f"replay R2 {r_first:.3f}->{r_last:.3f}; "
              f"teacher agreement {seed_entry['A']['teacher_R1_R2_agreement']:.4f}",
              flush=True)

    report["environment"] = {
        "python": platform.python_version(), "numpy": np.__version__,
        "torch": torch.__version__, "device": "cpu"}
    args.output.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    print(f"Results: {output.resolve()}", flush=True)


if __name__ == "__main__":
    main()