"""Pure revision-1 acceptance decisions; no sampling, training or pool search."""
from fractions import Fraction

import numpy as np

from .config import (
    ACCEPTANCE_COUNT, CLASS_BAND, CLASSES, DISAGREEMENT_BAND,
    EXCLUSION_PROPOSALS, MAX_EXCLUSION, MAX_PROPOSALS,
)


def _within(count, total, bounds):
    """Compare integer counts to exact decimal protocol bounds."""
    value = Fraction(int(count), int(total))
    return Fraction(str(bounds[0])) <= value <= Fraction(str(bounds[1]))


def _labels(values):
    values = np.asarray(values)
    if (values.shape != (ACCEPTANCE_COUNT, 2)
            or values.dtype.kind not in "iu"
            or np.any(values < 0) or np.any(values >= CLASSES)):
        raise ValueError("Expected 20000 accepted rows of two clean rule labels")
    return values


def assess_candidate(*, exclusion_masks, accepted_labels, proposal_counts,
                     budget_exhausted=()):
    """Evaluate both mixtures; absence of a measurement is never a pass.

    exclusion_masks: mixture -> boolean mask over 100000 independent proposals.
    accepted_labels: mixture -> 20000-by-2 clean labels on accepted inputs.
    proposal_counts: mixture -> number of proposals used for acceptance sampling.
    budget_exhausted: mixtures that failed to collect enough accepted samples
    after exactly the prescribed proposal ceiling. Their labels must be absent.

    Training data must not be used here. Stream independence and provenance
    belong to the sampling/recording runner, not this pure decision function.
    """
    exhausted = tuple(budget_exhausted)
    if (any(type(m) is not int or m not in (0, 1) for m in exhausted)
            or len(set(exhausted)) != len(exhausted)):
        raise ValueError("Invalid or duplicated budget-exhausted mixtures")
    exhausted = set(exhausted)
    for mapping in (exclusion_masks, accepted_labels, proposal_counts):
        if any(type(key) is not int or key not in (0, 1) for key in mapping):
            raise ValueError("Mixture keys must be integer zero or one")
    if set(exclusion_masks) != {0, 1} or set(proposal_counts) != {0, 1}:
        raise ValueError("Both mixtures require exclusion and proposal records")
    if set(accepted_labels) != {0, 1} - exhausted:
        raise ValueError("Missing labels or labels supplied for an exhausted mixture")

    reasons, mixtures = [], {}
    for mixture in (0, 1):
        mask = np.asarray(exclusion_masks[mixture])
        if mask.dtype != np.bool_ or mask.shape != (EXCLUSION_PROPOSALS,):
            raise ValueError("Exclusion audit requires 100000 boolean selections")
        proposals = proposal_counts[mixture]
        if type(proposals) is not int or not 0 < proposals <= MAX_PROPOSALS:
            raise ValueError("Invalid acceptance proposal count")
        excluded = EXCLUSION_PROPOSALS - int(mask.sum())
        exclusion_ok = _within(excluded, EXCLUSION_PROPOSALS, (0, MAX_EXCLUSION))
        row = {
            "exclusion_proposals": EXCLUSION_PROPOSALS,
            "excluded_count": excluded,
            "exclusion_fraction": excluded / EXCLUSION_PROPOSALS,
            "exclusion_passed": exclusion_ok,
            "acceptance_proposals": proposals,
            "budget_exhausted": mixture in exhausted,
            "accepted_sample_count": None,
            "class_counts": None,
            "class_fractions": None,
            "disagreement_count": None,
            "disagreement_fraction": None,
            "balance_passed": None,
            "disagreement_passed": None,
        }
        if not exclusion_ok:
            reasons.append({"mixture": mixture, "criterion": "exclusion"})
        if mixture in exhausted:
            if proposals != MAX_PROPOSALS:
                raise ValueError("Budget exhaustion requires the full proposal ceiling")
            reasons.append({"mixture": mixture, "criterion": "proposal_budget"})
        else:
            if proposals < ACCEPTANCE_COUNT:
                raise ValueError("Accepted sample count exceeds proposal count")
            labels = _labels(accepted_labels[mixture])
            counts = [np.bincount(labels[:, rule].astype(np.int64), minlength=CLASSES)
                      for rule in (0, 1)]
            balance_ok = all(_within(n, ACCEPTANCE_COUNT, CLASS_BAND)
                             for rule_counts in counts for n in rule_counts)
            disagreement = int(np.sum(labels[:, 0] != labels[:, 1]))
            disagreement_ok = _within(
                disagreement, ACCEPTANCE_COUNT, DISAGREEMENT_BAND)
            row.update({
                "accepted_sample_count": ACCEPTANCE_COUNT,
                "class_counts": [values.tolist() for values in counts],
                "class_fractions": [(values / ACCEPTANCE_COUNT).tolist()
                                    for values in counts],
                "disagreement_count": disagreement,
                "disagreement_fraction": disagreement / ACCEPTANCE_COUNT,
                "balance_passed": balance_ok,
                "disagreement_passed": disagreement_ok,
            })
            if not balance_ok:
                reasons.append({"mixture": mixture, "criterion": "balance"})
            if not disagreement_ok:
                reasons.append({"mixture": mixture, "criterion": "disagreement"})
        mixtures[f"M{mixture + 1}"] = row
    return {"accepted": not reasons, "reasons": reasons, "mixtures": mixtures}