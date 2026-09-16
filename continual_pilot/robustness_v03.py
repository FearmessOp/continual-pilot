"""Fixed 20-candidate design audit; does not select or replace a generator."""
import json
import platform
from pathlib import Path

import numpy as np
import torch

import generator_v03 as gv3


SEED_START = 1000
CANDIDATES = 20
METRIC_SEED_START = 50000
COUNT = 20000
SELECTED_SEED = 1000


def audit():
    """Evaluate every preregistered candidate, including those after acceptance."""
    records = []
    counts = {"accepted": 0, "balance_only": 0,
              "disagreement_only": 0, "both": 0}
    for index in range(CANDIDATES):
        seed = SEED_START + index
        metric_seed = METRIC_SEED_START + index
        generator = gv3.GeneratorV03(
            seed=seed, alpha=0.5, noise=0.05, calibration_count=COUNT)
        metrics = gv3.acceptance_metrics(
            generator, seed=metric_seed, count=COUNT)
        reasons = gv3.failure_reason(metrics)
        category = ("accepted" if not reasons else
                    "both" if len(reasons) == 2 else reasons[0] + "_only")
        counts[category] += 1
        records.append({
            "generator_seed": seed,
            "offset_seed": generator.offset_seed,
            "metric_seed": metric_seed,
            "accepted": not reasons,
            "reasons": reasons,
            "metrics": metrics,
        })
    return {
        "revision": "generator-v03-robustness",
        "selected_generator_seed_unchanged": SELECTED_SEED,
        "protocol": {
            "seed_start": SEED_START, "candidates": CANDIDATES,
            "metric_seed_start": METRIC_SEED_START,
            "count_per_mixture": COUNT, "alpha": 0.5, "noise": 0.05,
            "class_band": [gv3.CLASS_LOW, gv3.CLASS_HIGH],
            "disagreement_band": [gv3.DISAGREEMENT_LOW, gv3.DISAGREEMENT_HIGH],
            "early_stopping": False,
        },
        "counts": counts,
        "acceptance_rate": counts["accepted"] / CANDIDATES,
        "records": records,
        "limitations": [
            "Descriptive fraction over 20 fixed seeds, not a population guarantee.",
            "This audit does not select a new generator or train any learner.",
            "The original acceptance report remains unchanged.",
            "No extrapolation to the 200-attempt cap or multi-seed power.",
        ],
    }


def main():
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    report = audit()
    report["environment"] = {
        "python": platform.python_version(), "numpy": np.__version__,
        "torch": torch.__version__, "device": "cpu"}
    output = Path(__file__).parent / "results_robustness_v03" / "summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    print(json.dumps(report["counts"]))
    print(f"Acceptance rate: {report['acceptance_rate']:.1%}")
    print(f"Results: {output.resolve()}")


if __name__ == "__main__":
    main()