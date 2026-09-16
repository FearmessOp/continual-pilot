"""Role-separated recorded data builders; no data production on import."""
import copy

import numpy as np

from .config import CONTEXT_WINDOW, derive_seed
from .representation import BLOCKS_PER_RULE


def learner_seeds(section, pair):
    """Method-independent initialization/reset streams for paired conditions."""
    seeds = {}
    for expert in (0, 1):
        seeds[f"model{expert}"] = derive_seed(
            section, pair, f"model{expert}", expert=expert)
        seeds[f"cpr{expert}"] = derive_seed(
            section, pair, "cpr", expert=expert)
    for role in ("reservoir-replacement", "reservoir-sampling"):
        seeds[role] = derive_seed(section, pair, role)
    return seeds


def stationary_data(filtered, *, section, pair, role, condition, count):
    """Record one stationary stream and its exact proposal order/RNG state.

    condition 0 means M1/R1; condition 1 means M2/R2. This metadata belongs to
    the evaluator, not to the learner interface. Each condition has distinct
    role streams; methods share the returned data rather than resampling it.
    """
    if type(condition) is not int or condition not in (0, 1):
        raise ValueError("Stationary condition must be zero or one")
    if role not in ("training", "gate-calibration", "evaluation", "mapping"):
        raise ValueError("Invalid stationary data role")
    seed = derive_seed(section, pair, role, phase=condition + 1)
    rng = np.random.default_rng(seed)
    initial_rng = copy.deepcopy(rng.bit_generator.state)
    values, trace = filtered.sample_with_trace(count, condition, condition, rng)
    x, noisy, clean, z = values
    return {
        "arrays": {
            "x": x, "noisy": noisy, "clean": clean, "z": z,
            "r1": filtered.labels(z, 0),
            "r2": filtered.labels(z, 1),
            "index": np.arange(count, dtype=np.int64),
        },
        "trace": trace,
        "provenance": {
            "section": section, "pair": pair, "role": role,
            "condition": condition, "mixture": condition, "rule": condition,
            "seed": seed, "count": count,
            "rng_before": initial_rng,
            "rng_after": copy.deepcopy(rng.bit_generator.state),
        },
    }


def representation_data(filtered, *, section, pair, split):
    """Shared M2 inputs and independent rule-noise streams for one probe split.

    Training/evaluation have different role namespaces. Repeat 0 selects latent
    proposals; repeats 1 and 2 select R1 and R2 label noise respectively.
    Every numerical seed and before/after RNG state is returned for archiving.
    """
    roles = {
        "train": "representation-training",
        "test": "representation-evaluation",
    }
    if split not in roles:
        raise ValueError("Representation split must be train or test")
    role = roles[split]
    count = BLOCKS_PER_RULE * CONTEXT_WINDOW
    seeds = {
        "inputs": derive_seed(section, pair, role, repeat=0),
        "noise_r1": derive_seed(section, pair, role, repeat=1),
        "noise_r2": derive_seed(section, pair, role, repeat=2),
    }
    if len(set(seeds.values())) != len(seeds):
        raise AssertionError("Representation RNG seed collision")
    generators = {name: np.random.default_rng(seed) for name, seed in seeds.items()}
    before = {name: copy.deepcopy(rng.bit_generator.state)
              for name, rng in generators.items()}
    z, trace = filtered.accepted_latents(count, 1, generators["inputs"])
    clean = np.column_stack([filtered.labels(z, rule) for rule in (0, 1)])
    noisy = clean.copy()
    for rule in (0, 1):
        rng = generators[f"noise_r{rule + 1}"]
        flip = rng.random(count) < filtered.teacher.noise
        offsets = rng.integers(1, 4, size=count)
        noisy[:, rule] = np.where(flip, (clean[:, rule] + offsets) % 4, clean[:, rule])
    return {
        "arrays": {
            "x": (z @ filtered.teacher.w.T).astype(np.float32),
            "z": z, "clean_by_rule": clean, "noisy_by_rule": noisy,
            "index": np.arange(count, dtype=np.int64),
        },
        "trace": trace,
        "provenance": {
            "section": section, "pair": pair, "role": role, "split": split,
            "mixture": 1, "count": count, "seeds": seeds,
            "rng_before": before,
            "rng_after": {name: copy.deepcopy(rng.bit_generator.state)
                          for name, rng in generators.items()},
        },
    }