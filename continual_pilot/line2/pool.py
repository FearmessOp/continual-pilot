"""Recorded control-pool acceptance; invoked explicitly only after prerequisites.

No CLI, training, duration/power/main pool, or experiment runs on import.
The caller must archive sources/environment and successful test evidence before
calling run_control_pool. Generator selection never receives learner results.
"""
import copy
import time
from collections import Counter

import numpy as np

from .acceptance import assess_candidate
from .config import (
    ACCEPTANCE_COUNT, ACTIVE_REVISION, CALIBRATION_COUNT, CONTROL_PAIRS,
    CONTROL_POOL_START, EXCLUSION_PROPOSALS, MARGIN_THRESHOLD, MAX_CANDIDATES,
    derive_seed, verify_v05_protocol as verify_protocol,
)
from .filtering import JointMarginFilter, ProposalBudgetExceeded
from .teacher import RecordedTeacher


def candidate_seeds(attempt):
    """Sequential teacher IDs; independent role seeds indexed by candidate ID.

    Pool starts specify actual teacher seeds, not hashes of those seeds.
    Offset/scale/audit streams use the semantic hierarchy from revision 1.
    Accepted pair indices are assigned separately, in acceptance order.
    """
    if type(attempt) is not int or not 0 <= attempt < MAX_CANDIDATES:
        raise ValueError("Control candidate index outside the locked pool")
    teacher_seed = CONTROL_POOL_START + attempt
    return {
        "teacher": teacher_seed,
        "offset": derive_seed("control", teacher_seed, "offset"),
        "scale": derive_seed("control", teacher_seed, "scale"),
        "exclusion": [
            derive_seed("control", teacher_seed, "exclusion", repeat=mixture)
            for mixture in (0, 1)
        ],
        "acceptance": [
            derive_seed("control", teacher_seed, "acceptance", repeat=mixture)
            for mixture in (0, 1)
        ],
    }


def save_trace(records, directory, trace):
    arrays = {key: value for key, value in trace.items()
              if isinstance(value, np.ndarray)}
    metadata = {key: value for key, value in trace.items()
                if not isinstance(value, np.ndarray)}
    records.arrays(f"{directory}/proposals.npz", arrays)
    records.json(f"{directory}/proposal_counts.json", metadata)


def evaluate_candidate(records, *, attempt):
    """Construct, audit and archive one candidate without any learner access."""
    seeds = candidate_seeds(attempt)
    directory = f"candidates/teacher{seeds['teacher']}"
    # Write the complete candidate seed plan before its first random draw.
    records.json(f"{directory}/seeds.json", seeds)
    started = time.perf_counter()
    teacher = RecordedTeacher(
        teacher_seed=seeds["teacher"], offset_seed=seeds["offset"])
    records.arrays(f"{directory}/teacher.npz", teacher.archive_arrays())
    records.json(f"{directory}/teacher_provenance.json", teacher.provenance())

    scale_rng = np.random.default_rng(seeds["scale"])
    scale_before = copy.deepcopy(scale_rng.bit_generator.state)
    scale_z = teacher._mixed_z(scale_rng, CALIBRATION_COUNT)
    filtered = JointMarginFilter(teacher, scale_latents=scale_z)
    records.arrays(f"{directory}/margin_scale.npz", {
        "unfiltered_equal_mixture_z": scale_z,
        "scales": filtered.scales.copy(),
    })
    records.json(f"{directory}/scale_rng.json", {
        "before": scale_before,
        "after": copy.deepcopy(scale_rng.bit_generator.state),
        "mixture_order": ["M1", "M2"],
        "rows_per_mixture": CALIBRATION_COUNT // 2,
    })

    masks, labels, proposal_counts, exhausted = {}, {}, {}, []
    for mixture in (0, 1):
        prefix = f"{directory}/M{mixture + 1}"
        exclusion_rng = np.random.default_rng(seeds["exclusion"][mixture])
        before = copy.deepcopy(exclusion_rng.bit_generator.state)
        z = filtered.proposals(EXCLUSION_PROPOSALS, mixture, exclusion_rng)
        margins = filtered.normalized_margins(z)
        masks[mixture] = filtered.keep(z)
        records.arrays(f"{prefix}/exclusion.npz", {
            "proposal_z": z, "normalized_margins": margins,
            "keep": masks[mixture],
            "index": np.arange(EXCLUSION_PROPOSALS, dtype=np.int64),
        })
        records.json(f"{prefix}/exclusion_rng.json", {
            "before": before,
            "after": copy.deepcopy(exclusion_rng.bit_generator.state),
        })

        acceptance_rng = np.random.default_rng(seeds["acceptance"][mixture])
        before = copy.deepcopy(acceptance_rng.bit_generator.state)
        try:
            accepted_z, trace = filtered.accepted_latents(
                ACCEPTANCE_COUNT, mixture, acceptance_rng)
        except ProposalBudgetExceeded as error:
            trace = error.trace
            exhausted.append(mixture)
        else:
            labels[mixture] = np.column_stack([
                filtered.labels(accepted_z, rule) for rule in (0, 1)
            ])
            records.arrays(f"{prefix}/accepted.npz", {
                "z": accepted_z,
                "clean_by_rule": labels[mixture],
                "index": np.arange(ACCEPTANCE_COUNT, dtype=np.int64),
            })
        proposal_counts[mixture] = trace["proposed_count"]
        save_trace(records, f"{prefix}/acceptance", trace)
        records.json(f"{prefix}/acceptance_rng.json", {
            "before": before,
            "after": copy.deepcopy(acceptance_rng.bit_generator.state),
        })
    report = assess_candidate(
        exclusion_masks=masks, accepted_labels=labels,
        proposal_counts=proposal_counts, budget_exhausted=exhausted)
    report.update({
        "attempt_one_based": attempt + 1,
        "teacher_seed": seeds["teacher"],
        "artifact_directory": directory,
        "seconds": time.perf_counter() - started,
    })
    records.json(f"{directory}/decision.json", report)
    return report, filtered


def run_control_pool(records):
    """Select first three accepted generators in at most 200 ordered attempts."""
    verify_protocol()
    reports, accepted = [], []
    reasons = Counter()
    started = time.perf_counter()
    for attempt in range(MAX_CANDIDATES):
        report, filtered = evaluate_candidate(records, attempt=attempt)
        reports.append(report)
        if report["accepted"]:
            accepted.append({
                "pair": len(accepted),
                "teacher_seed": report["teacher_seed"],
                "candidate_report": report,
                "filtered": filtered,
            })
        else:
            # Count each failed criterion once per candidate, not per mixture.
            reasons.update({item["criterion"] for item in report["reasons"]})
        print(f"Control candidate {report['teacher_seed']}: "
              f"accepted={report['accepted']}, reasons={report['reasons']}", flush=True)
        if len(accepted) == CONTROL_PAIRS:
            break
    summary = {
        "active_revision": ACTIVE_REVISION,
        "margin_threshold": MARGIN_THRESHOLD,
        "teacher_pool_start": CONTROL_POOL_START,
        "maximum_candidates": MAX_CANDIDATES,
        "final_scientific_attempt": True,
        "accepted": len(accepted) == CONTROL_PAIRS,
        "required_generators": CONTROL_PAIRS,
        "accepted_generators": [
            {"pair": item["pair"], "teacher_seed": item["teacher_seed"]}
            for item in accepted
        ],
        "attempts_tried": len(reports),
        "rejected_count": len(reports) - len(accepted),
        "rejected_candidates_by_criterion": dict(sorted(reasons.items())),
        "candidate_reports": reports,
        "seconds": time.perf_counter() - started,
        "next_action": ("stationary_controls_only" if len(accepted) == CONTROL_PAIRS
                        else "stop_for_user_no_gate"),
        "learner_performance_used_for_selection": False,
    }
    records.json("acceptance_summary.json", summary)
    return summary, accepted