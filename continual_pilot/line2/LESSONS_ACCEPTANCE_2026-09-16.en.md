# Design lesson after v0.4 acceptance

English translation of the [Turkish original](LESSONS_ACCEPTANCE_2026-09-16.md).
Publication note: this is a historical post-v0.4 assessment. Its discussion of
a possible next version is not current permission; the final v0.5 attempt has
since completed and the research line is closed.

Date: 2026-09-16.
Status: post-result assessment; neither a new preregistration nor execution permission.

## Observation and design responsibility

All 200 candidates recorded in the [results report](REPORT_CONTROL_V04_01.md)
exceeded the 30% exclusion ceiling for M1. Minimum exclusion was 30.080%,
with a median of 46.2445%. The normalized margin threshold of 0.25 and the
30% exclusion ceiling were not jointly satisfied in this pool.
The process was stopped without relaxing the ceiling.

Calling this merely a generator-search failure incompletely describes the
design problem: the filter threshold and exclusion ceiling are coupled and
should have been examined jointly with the existing margin diagnostic before
locking. That compatibility check was not performed. However, failure in a
finite pool does not prove that the two numbers are mathematically inconsistent
for all possible generators.

## Approximate calculation that should have preceded locking

An input having a below-threshold margin under either R1 or R2 is sufficient
for exclusion by the joint filter. Therefore:

Joint exclusion = p1 + p2 − probability of the intersection of the two low-margin events.

Assuming the two events are independent and p1 = p2 = p:

Joint exclusion ≈ 1 − (1 − p)².

Using the owner's approximate p = 27%, this gives about 46.71%, consistent
with the observed median of about 46%.
Here, 27% is the value used in the owner's approximate calculation, not a
measurement reverified from the earlier report when this note was prepared.

The [earlier margin report](../results_margin_v03/summary.json) reported
a 12.17% share with normalized margin <0.1 for v0.3.
The same independence and equal-marginal-probability approximation predicts
about 22.86% joint exclusion for this value.

These calculations could have provided a warning and compatibility check
before locking. The two rules share a common teacher component; independence
cannot be assumed. An earlier single-rule/distribution measurement cannot be
transferred directly to both rules and both mixtures in the new teacher pool.
22.86% is not an acceptance guarantee.

## A second signal concerning balance

156 candidates were rejected for balance and exclusion; another 5 were
rejected for balance, disagreement, and exclusion.
There were balance violations in 161 candidates in total.

Conditioning on margin can change class shares; low-margin mass need not be
equally distributed across classes. The observation is consistent with this
explanation. However, without a paired comparison against the same candidates'
unfiltered class shares, it cannot be established that filtering caused every
balance violation. A lower threshold may alleviate balance problems, but does
not guarantee doing so.

## Recorded lesson

Coupled preregistration parameters should not be locked as individually
“reasonable numbers” without a joint compatibility check using existing
diagnostic data.

The check should explicitly state its assumptions, the data partition used,
joint-event probability, differences between mixtures, and uncertainty.
Designing from existing diagnostic data must be distinguished from changing
the same version's success boundary after seeing its results.

## A next version that could be considered only by user decision

The single candidate proposed by the owner is a normalized margin threshold
of 0.1. The choice is motivated by the existing generator margin diagnostic,
not a student-training result. Trial-and-error threshold search is not proposed.

If a new revision is approved, the class band and 30% exclusion ceiling remain.
If acceptance fails again, abandoning the filtering approach and reconsidering
the gate definition could be proposed; no automatic gate change or gate run occurs.

The previous control-pool results have now been seen. A future revision must
explicitly state whether it reuses the pool or selects a new one;
an already-seen pool must not be presented as independent new confirmation data.

This note does not change the threshold, approve a new revision, or select seeds.
This round runs no acceptance, training, tests, diagnostics, duration pilot,
power pilot, or main experiment. Scientific work is paused at the user-decision stage.