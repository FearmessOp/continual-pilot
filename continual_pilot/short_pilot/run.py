"""Short exploratory pilot: reuse the validated engine, never tune after results."""
import argparse
import copy
import json
import math
import platform
import shutil
import sys
from pathlib import Path

import numpy as np
import torch

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from asymmetric_pilot.engine import CONFIG as BASE_CONFIG, select_candidate
from asymmetric_pilot.run import Records, file_digest, run_pilot


CONFIG = copy.deepcopy(BASE_CONFIG)
CONFIG.update(
    stream_seeds=[240001, 240002, 240003],
    phase3_candidates=[1024, 1536],
    evaluation_seed=249001,
    minimum_phase2_accuracy=0.86,
)


def decide(rows, config):
    """Validate complete A rows, then apply the prospectively recorded tree."""
    expected = {(seed, length) for seed in config["stream_seeds"]
                for length in config["phase3_candidates"]}
    a_rows = [row for row in rows if row["method"] == "A"]
    keys = [(row["seed"], row["phase3_count"]) for row in a_rows]
    if len(keys) != len(expected) or set(keys) != expected:
        raise ValueError("Missing, unexpected or duplicated A rows")
    for row in a_rows:
        accuracy = row["frozen"]["2"]["r1_accuracy"]
        if not math.isfinite(accuracy) or not 0 <= accuracy <= 1:
            raise ValueError("Invalid phase-2 accuracy")
        if not math.isfinite(row["damage"]) or not -1 <= row["damage"] <= 1:
            raise ValueError("Invalid damage")
    for seed in config["stream_seeds"]:
        references = {row["frozen"]["2"]["r1_accuracy"]
                      for row in a_rows if row["seed"] == seed}
        if len(references) != 1:
            raise ValueError("Candidates must share their phase-2 reference")

    selection = select_candidate(rows, config)
    baseline_ok = all(
        row["frozen"]["2"]["r1_accuracy"] >= config["minimum_phase2_accuracy"]
        for row in a_rows)
    next_candidate = None
    if not baseline_ok:
        selection["selected_phase3_count"] = None
        selection["eligible_candidates"] = []
        status = "phase2_control_failed"
    elif selection["selected_phase3_count"] is not None:
        status = "selected"
    elif all(row["damage"] < config["damage_band"][0] for row in a_rows):
        status, next_candidate = "all_below_band", 1792
    elif all(row["damage"] > config["damage_band"][1] for row in a_rows):
        status, next_candidate = "all_above_band", 768
    else:
        status = "mixed_no_selection"
    return {
        **selection,
        "phase2_control_passed": baseline_ok,
        "status": status,
        "suggested_future_candidate": next_candidate,
        "future_candidate_executed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=PROJECT / "short_pilot" / "results")
    args = parser.parse_args()
    records = Records(args.output)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    sources = [
        Path("short_pilot/run.py"), Path("short_pilot/PROTOCOL.md"),
        Path("asymmetric_pilot/run.py"), Path("asymmetric_pilot/engine.py"),
        Path("pilot.py"), Path("diagnose.py"), Path("generator_v03.py"),
        Path("test_short_pilot.py"), Path("test_asymmetric_pilot.py"),
    ]
    for relative in sources:
        source = PROJECT / relative
        destination = records.root / "sources" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        records.files[destination.relative_to(records.root).as_posix()] = {
            "sha256": file_digest(destination)}
    config = copy.deepcopy(CONFIG)
    records.json("protocol.json", config)
    report = run_pilot(records, config)
    report["revision"] = "short-pilot-1024-1536"
    report["selection"] = decide(report["rows"], config)
    report["environment"] = {
        "python": platform.python_version(), "numpy": np.__version__,
        "torch": torch.__version__, "device": "cpu", "threads": 1}
    records.json("summary.json", report)
    records.finish()
    print(json.dumps(report["selection"]), flush=True)
    print(f"Results: {records.root.resolve()}", flush=True)


if __name__ == "__main__":
    main()