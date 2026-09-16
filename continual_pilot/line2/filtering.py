"""Joint v0.4 margin filtering around an explicitly supplied v0.3 teacher.

Construction requires independently sampled, UNFILTERED scale-calibration
latents. This module neither selects teachers nor starts acceptance/training.
The caller archives the teacher, calibration latents, seeds and returned traces.
"""
import numpy as np

from .config import CALIBRATION_COUNT, MARGIN_THRESHOLD, MAX_PROPOSALS


PROPOSAL_CHUNK = 4096  # Numerical sampling layout; record in the run manifest.


def latent_matrix(z):
    array = np.asarray(z)
    if (array.dtype != np.float64 or array.ndim != 2 or array.shape[1] != 8
            or not np.isfinite(array).all()):
        raise ValueError("Expected finite full-precision float64 latent rows")
    return array


def score_margins(scores):
    """Largest minus second-largest score, without rounding or class averaging."""
    scores = np.asarray(scores)
    if (scores.ndim != 2 or scores.shape[1] != 4
            or not np.isfinite(scores).all()):
        raise ValueError("Expected four finite teacher scores per row")
    top = np.partition(scores, -2, axis=1)[:, -2:]
    return top[:, 1] - top[:, 0]


class ProposalBudgetExceeded(RuntimeError):
    def __init__(self, trace):
        super().__init__("Insufficient accepted examples within the proposal budget")
        self.trace = trace


class JointMarginFilter:
    """Fixed joint filter; noisy labels are generated only after selection.

    The underlying teacher is owned by this wrapper and must not be mutated.
    Both rule scales use the same independent equal-M1/M2 latent calibration.
    Scale is population std over ALL combined score elements, including offsets,
    matching the previously defined normalized teacher-margin diagnostic.
    """

    def __init__(self, teacher, *, scale_latents):
        import copy
        z = latent_matrix(scale_latents)
        if len(z) != CALIBRATION_COUNT:
            raise ValueError("Revision 1 requires exactly 20000 scale-calibration rows")
        self.teacher = copy.deepcopy(teacher)
        self.scales = np.asarray([
            self.scores(z, rule).std(ddof=0) for rule in (0, 1)
        ], dtype=np.float64)
        if not np.isfinite(self.scales).all() or np.any(self.scales <= 0):
            raise ValueError("Nonpositive or nonfinite margin normalization scale")
        self.scales.setflags(write=False)

    def scores(self, z, rule):
        if type(rule) is not int or rule not in (0, 1):
            raise ValueError("Rule must be zero or one")
        z = latent_matrix(z)
        scores = self.teacher._base_scores(z, rule) + self.teacher.offsets[rule]
        if scores.shape != (len(z), 4) or not np.isfinite(scores).all():
            raise ValueError("Invalid teacher scores")
        return scores

    def labels(self, z, rule):
        return self.scores(z, rule).argmax(axis=1)

    def normalized_margins(self, z):
        return np.column_stack([
            score_margins(self.scores(z, rule)) / self.scales[rule]
            for rule in (0, 1)
        ])

    def keep(self, z):
        return np.all(self.normalized_margins(z) >= MARGIN_THRESHOLD, axis=1)

    def proposals(self, count, mixture, rng):
        if type(count) is not int or count < 1:
            raise ValueError("Proposal count must be a positive integer")
        if type(mixture) is not int or mixture not in (0, 1):
            raise ValueError("Mixture must be zero or one")
        components = rng.choice(4, size=count, p=self.teacher.weights[mixture])
        return rng.normal(size=(count, 8)) + self.teacher.means[components]

    def accepted_latents(self, count, mixture, rng, *, max_proposals=MAX_PROPOSALS):
        """Draw in fixed chunks, retaining first accepted rows in proposal order.

        Each chunk is at most the remaining requested count. Thus no accepted
        rows are silently discarded and the archived proposal count is exact.
        A shortfall raises with complete proposal/selection trace, never widens
        the filter or returns a shorter dataset as successful.
        """
        if type(count) is not int or not 0 < count <= MAX_PROPOSALS:
            raise ValueError("Invalid requested accepted sample count")
        if (type(max_proposals) is not int
                or not 0 < max_proposals <= MAX_PROPOSALS):
            raise ValueError("Invalid proposal budget")
        pieces, masks, selected = [], [], []
        proposed = accepted = 0
        while accepted < count and proposed < max_proposals:
            size = min(PROPOSAL_CHUNK, count - accepted, max_proposals - proposed)
            z = self.proposals(size, mixture, rng)
            mask = self.keep(z)
            pieces.append(z)
            masks.append(mask)
            selected.append(z[mask])
            proposed += size
            accepted += int(mask.sum())
        trace = {
            "proposal_z": np.concatenate(pieces),
            "keep": np.concatenate(masks),
            "accepted_proposal_indices": np.flatnonzero(np.concatenate(masks)),
            "proposed_count": proposed,
            "accepted_count": accepted,
            "requested_count": count,
            "max_proposals": max_proposals,
        }
        if accepted != count:
            raise ProposalBudgetExceeded(trace)
        return np.concatenate(selected), trace

    def sample_with_trace(self, count, mixture, rule, rng):
        if type(rule) is not int or rule not in (0, 1):
            raise ValueError("Rule must be zero or one")
        z, trace = self.accepted_latents(count, mixture, rng)
        clean = self.labels(z, rule)
        flip = rng.random(count) < self.teacher.noise
        offsets = rng.integers(1, 4, size=count)
        noisy = np.where(flip, (clean + offsets) % 4, clean)
        x = (z @ self.teacher.w.T).astype(np.float32)
        return (x, noisy, clean, z), trace

    def sample(self, count, mixture, rule, rng):
        """Compatibility interface; production recording should use sample_with_trace."""
        values, _ = self.sample_with_trace(count, mixture, rule, rng)
        return values