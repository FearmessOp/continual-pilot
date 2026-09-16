"""Pure stationary-gate metrics; never trains, samples or changes a learner."""
import math
from fractions import Fraction

import numpy as np

from .config import CALIBRATION_COUNT, CLASSES, EVALUATION_COUNT, GATE_FRACTION


def class_vector(values):
    array = np.asarray(values)
    if (array.ndim != 1 or not len(array) or array.dtype.kind not in "iu"
            or np.any(array < 0) or np.any(array >= CLASSES)):
        raise ValueError("Expected a nonempty vector of integer class indices")
    return array.astype(np.int64, copy=False)


def wilson_interval(correct, total):
    """Two-sided nominal 95% Wilson interval; historical convention z=1.96."""
    if (type(correct) is not int or type(total) is not int
            or total <= 0 or not 0 <= correct <= total):
        raise ValueError("Invalid binomial counts")
    z = 1.96
    proportion = correct / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(
        proportion * (1 - proportion) / total
        + z * z / (4 * total * total)) / denominator
    return [max(0.0, center - radius), min(1.0, center + radius)]


def classification(predictions, clean):
    predictions, clean = class_vector(predictions), class_vector(clean)
    if predictions.shape != clean.shape:
        raise ValueError("Prediction and clean-target shapes differ")
    confusion = np.bincount(
        CLASSES * clean + predictions, minlength=CLASSES * CLASSES
    ).reshape(CLASSES, CLASSES)
    support = confusion.sum(axis=1)
    correct = int(np.trace(confusion))
    return {
        "count": len(clean),
        "correct": correct,
        "clean_accuracy": correct / len(clean),
        "clean_wilson_95": wilson_interval(correct, len(clean)),
        "wilson_z": 1.96,
        "confusion_matrix_true_by_pred": confusion.tolist(),
        "class_support": support.tolist(),
        "per_class_recall": [
            int(confusion[i, i]) / int(support[i]) if support[i] else None
            for i in range(CLASSES)
        ],
    }


def stationary_gate(predictions, clean, calibration_clean):
    """Pass only when the Wilson LOWER bound strictly exceeds measured threshold.

    Inputs must come from the separately recorded calibration/test streams.
    Stream provenance cannot be inferred from target vectors and must be
    verified by the runner. Neither overlap nor insufficient precision allows
    extra samples, a replacement learner, or a relaxed threshold.
    """
    calibration = class_vector(calibration_clean)
    if len(calibration) != CALIBRATION_COUNT:
        raise ValueError("Gate calibration requires exactly 20000 examples")
    report = classification(predictions, clean)
    if report["count"] != EVALUATION_COUNT:
        raise ValueError("Frozen gate evaluation requires exactly 20000 examples")
    counts = np.bincount(calibration, minlength=CLASSES)
    baseline = Fraction(int(counts.max()), len(calibration))
    threshold = baseline + Fraction(str(GATE_FRACTION)) * (1 - baseline)
    low, high = report["clean_wilson_95"]
    # Compare the computed bound with the exact rational threshold, no rounding.
    passed = Fraction.from_float(low) > threshold
    comparison = ("passed" if passed else
                  "below_threshold" if Fraction.from_float(high) < threshold
                  else "interval_overlaps_threshold")
    return {
        **report,
        "calibration_count": len(calibration),
        "calibration_class_counts": counts.tolist(),
        "calibration_majority_class": int(counts.argmax()),
        "calibration_majority_accuracy": float(baseline),
        "threshold": float(threshold),
        "threshold_numerator": threshold.numerator,
        "threshold_denominator": threshold.denominator,
        "passed": passed,
        "comparison": comparison,
        "required_action": "await_remaining_controls" if passed else "stop_for_user",
        "interval_scope": (
            "Conditional on the trained learner and measured threshold; "
            "does not include training-seed or threshold-calibration uncertainty."
        ),
    }


def online_curve(predictions, noisy, clean, *, block=1000):
    """Nonoverlapping prequential blocks, NOT frozen end-of-block accuracy."""
    predictions, noisy, clean = (
        class_vector(values) for values in (predictions, noisy, clean))
    if not predictions.shape == noisy.shape == clean.shape:
        raise ValueError("Online prediction and target shapes differ")
    if type(block) is not int or block <= 0:
        raise ValueError("Curve block size must be a positive integer")
    regret = ((predictions != noisy).astype(np.int64)
              - (clean != noisy).astype(np.int64))
    rows = []
    for start in range(0, len(clean), block):
        stop = min(start + block, len(clean))
        rows.append({
            "start_index": start,
            "stop_index_exclusive": stop,
            "count": stop - start,
            "online_clean_accuracy": float(np.mean(
                predictions[start:stop] == clean[start:stop])),
            "online_noisy_accuracy": float(np.mean(
                predictions[start:stop] == noisy[start:stop])),
            "oracle_regret": int(regret[start:stop].sum()),
            "oracle_regret_per_example": float(regret[start:stop].mean()),
        })
    return rows