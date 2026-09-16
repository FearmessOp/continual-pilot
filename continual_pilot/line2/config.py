"""Locked Line 2 constants and deterministic, role-separated seed derivation.

Importing this module does not generate experimental data or train a model.
A matching document hash establishes content integrity, not execution permission
or a verified Bitcoin timestamp.
"""
import hashlib
from pathlib import Path

import numpy as np


PROTOCOL_PATH = Path(__file__).with_name("PREREGISTRATION_DRAFT.md")
PROTOCOL_SHA256 = (
    "0800b0647a0feec22dc13b83ddfaaa7478dc4cd8fe54d3a923423f3cd8d136f7"
)
ROOT_SEED = 20260916
SEED_SCHEMA = "line2-revision1-role-seeds-v1"

INPUT_DIM = 32
HIDDEN_DIM = 64
CLASSES = 4
CONTEXT_WINDOW = 64
CONTEXT_DIM = 132
EXPERTS = 2
MINIBATCH = 16
LEARNING_RATE = 0.001
ADAM_BETAS = (0.9, 0.999)
ADAM_EPSILON = 1e-8

EXPLORATION_PERIOD = 8
CPR_PERIOD = 8
CPR_EMA_DECAY = 0.99
CPR_MAX_RESET = 0.01
CPR_STEEPNESS = 4.0
CPR_EPSILON = 1e-8
CPR_ACTIVITY_MINIMUM = 0.001

REPLAY_CAPACITY = 512
REPLAY_PER_NEW = 8
KNN_WINDOW = 256
KNN_NEIGHBORS = 5

MARGIN_THRESHOLD = 0.25
MAX_EXCLUSION = 0.30
CLASS_BAND = (0.18, 0.35)
DISAGREEMENT_BAND = (0.40, 0.70)
CALIBRATION_COUNT = 20000
EXCLUSION_PROPOSALS = 100000
ACCEPTANCE_COUNT = 20000
MAX_PROPOSALS = 1000000
MAX_CANDIDATES = 200
CONTROL_POOL_START = 10000
CONTROL_PAIRS = 3
TRAIN_COUNT = 40000
EVALUATION_COUNT = 20000
GATE_FRACTION = 0.9

ROLES = frozenset({
    "teacher", "offset", "scale", "acceptance", "exclusion",
    "model0", "model1", "training", "cpr",
    "reservoir-replacement", "reservoir-sampling",
    "mapping", "evaluation", "gate-calibration",
    "representation-training", "representation-evaluation",
    "power", "bootstrap",
})
SECTIONS = frozenset({"mechanics-test", "control", "duration", "power", "main"})


def verify_protocol(path=PROTOCOL_PATH):
    """Fail closed if the approved protocol bytes have changed."""
    actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual != PROTOCOL_SHA256:
        raise ValueError(
            f"Locked protocol mismatch: expected {PROTOCOL_SHA256}, got {actual}"
        )
    return actual


def derive_seed(section, pair, role, *, phase=0, expert=0, repeat=0):
    """Return a reproducible 64-bit seed for an explicit semantic role.

    The UTF-8 schema/section/role digest supplies a stable namespace; numerical
    indices supply the hierarchy. No process-dependent hash, global RNG use,
    or order-dependent spawning is involved. Record returned seeds in manifests.
    """
    if section not in SECTIONS or role not in ROLES:
        raise ValueError("Unknown seed section or role")
    indices = (pair, phase, expert, repeat)
    if any(type(index) is not int or index < 0 for index in indices):
        raise ValueError("Seed indices must be nonnegative Python integers")
    namespace = f"{SEED_SCHEMA}\0{section}\0{role}".encode("utf-8")
    digest = hashlib.sha256(namespace).digest()
    words = [int.from_bytes(digest[i:i + 4], "little")
             for i in range(0, len(digest), 4)]
    sequence = np.random.SeedSequence([ROOT_SEED, *words, *indices])
    return int(sequence.generate_state(1, dtype=np.uint64)[0])