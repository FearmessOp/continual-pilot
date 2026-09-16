# Line 2 — Approved preregistration, revision 1

**Non-normative translation; the locked Turkish file is authoritative.**
Authoritative source: [locked Turkish protocol](PREREGISTRATION_DRAFT.md).
Authoritative source SHA-256:
0800b0647a0feec22dc13b83ddfaaa7478dc4cd8fe54d3a923423f3cd8d136f7

Publication note, outside the translated protocol: the research line is now
closed. The historical plans and permissions below describe revision 1, not
current authorization. See the [final results](FINAL_RESULTS_AND_LESSONS.en.md).
The original Bitcoin attestation does not timestamp this translation.
Decimal commas are rendered as decimal points; thousands separators are omitted.

---

Status: APPROVED BY THE USER; content locked. This is not execution permission.
Approval date: 2026-09-16. SHA-256 and Git records are kept in a separately dated lock record.
The filename was retained from the draft history; this heading states the valid status.
Date: 2026-09-16.
Label: Exploration-derived, preregistered confirmation on new data.
This round produces documentation only; no training, acceptance, power pilot, or main experiment.

## 1. Purpose and limits of existing evidence

Purpose: test whether routing and renewal together produce better results than
the learning–retention trade-off obtained merely by reducing update frequency.
Low forgetting alone is not success.

The selected exploratory v0.3 schedule is 40000/10000/1024/4000 examples.
Phase 3 has a budget of 64 update opportunities of 16 examples each;
the phase-4 transition window is 480 examples, or 30 opportunities.
Opportunities and actual updates are counted separately.
The v0.3 learnability gate has not passed; these data cannot start a confirmatory run.
The duration choice cannot be transferred to the v0.4 filtered distribution without revalidation.

An online block average does not represent block-end frozen accuracy during rapid change.
The earlier first-block 71.1% and the short pilot's final-state 58.660–61.530%
illustrate this distinction. Because preparation durations and seeds also differ,
the entire difference is not causally attributed to block averaging.
Duration and damage decisions use independent frozen measurements only.

## 2. Data access and common learner

Phase order: M1/R1 → M2/R1 → M2/R2 → M2/R1.
Base learner: 32→64→4, ReLU; Adam with fixed learning rate 0.001.
Minibatch: 16 new examples. Adam coefficients 0.9/0.999, epsilon 10^-8,
no weight penalty. Clean labels and true phase/rule identities are not supplied
to the predictions or updates of learned methods.
Each prediction is produced before the current noisy label is seen.

Context: only four class frequencies and four class-conditioned 32-dimensional
means of the last 64 observed noisy-label pairs; 132 dimensions in total.
The window is not reset at phase boundaries. The current observation is the experts' input.
The evaluator may access clean R1/R2 targets and is kept separate from training code.

## 3. Conditions

| Condition | Routing | Renewal | Description |
|---|---|---|---|
| A | No | No | One base learner |
| B | Yes | No | Two experts and a causal router |
| C | No | Yes | A + CPR-style adaptation |
| D | Yes | Yes | B + the same CPR-style adaptation |
| Replay | No | No | Reservoir 512; at most 8 historical examples per new example |
| Frozen-F2 | No | No | A's phase-2 copy; no updates in phases 3–4 |
| Sparse-A-50 | No | No | Update every second group in phases 3–4 |
| Sparse-A-25 | No | No | Update every fourth group in phases 3–4 |
| Sparse-A-75 | No | No | Skip every fourth group; calibration diagnostic only, not an envelope point |
| Recent k-NN | No | No | Most recent 256 noisy-label examples |
| A+context | No | No | 164→64→4; diagnostic of access to the same 132-dimensional summary |
| Regime-aware replay diagnostic | No | No | Same learner as replay; additional provenance records in the evaluator |

A/B/C/D are the primary 2×2 family. Other conditions are not included in the main factors.
Frozen-F2 and sparse-A branch from the same A phase-2 model and optimizer state.
B/D expert 0 initialization is paired with A/C initialization; expert 1 has a
separate initialization that is shared between B and D. C/D CPR randomness is paired.
B/D have more capacity: results are not presented as a pure capacity-independent
routing effect. A+context also changes the parameter count.

## 4. Router — approved mechanics

Two experts, each 32→64→4; no capacity enlargement or additional experts.
The router produces 132→2 linear scores; initial weights and biases are zero.
Router Adam learning rate is 0.001, with the experts' other Adam settings.
No normalization using future data; the standard context definition is used unchanged.

At the beginning of each group of 16, one expert is selected using the summary
of preceding history; the selection stays fixed throughout the group.
Ties choose the smaller expert index.
Every eighth global group uses exploration: expert indices alternate 0,1,0,1
across these groups. The global group counter does not know phase boundaries.
Exploration groups operate from phase 1 onward and are not disabled based on results.

Both experts' pre-update scores are computed for every example;
only the selected expert supplies the actual prediction.
After the label arrives, both experts' noisy cross-entropies are computed in
training logic, not evaluator logic. Each expert's mean loss is computed at group end.
The lowest-loss expert is the router's group target; ties choose the smaller index.
The router takes one step on the summary saved at group start with this target.
Only the selected expert takes one Adam step on the same 16 noisy examples.
The other expert receives no optimizer step or weight penalty.
Expert losses are computed before the expert update.
Spontaneous specialization is not assumed; collapse, expert starvation, and
failure to adapt within 64 opportunities are possible failures to report.

### Correct expert-mapping rule

True rule identity is not the router target.
The primary routing diagnostic is selection accuracy relative to the expert
with the lowest pre-update noisy group loss, with ties choosing the smaller index.
This diagnostic does not prove learning of the clean rule.

A separate clean expert–rule mapping is performed only in the evaluator:
at phase-3 end, both experts are evaluated against R1/R2 on 20000 M2 calibration
inputs separate from the main evaluation. Of the two possible one-to-one mappings,
choose the one with higher total clean accuracy; ties choose expert0→R1.
The mapping then remains fixed and is not reoptimized on the phase-4 test.
This post-training diagnostic mapping is not fed back into training-time routing.
Ideal routing selects among the same frozen experts; it does not train new experts.
If both experts are poor on both rules, mapping does not hide this: all four
accuracies and the best-expert error are also published.

### Diagnostics separating specialization from archive-like retention

The router is not assumed to remain zero in stationary phases:
different expert losses may produce different learning targets.
Expert 1 updating only through exploration is also a possibility to test, not a result.
In the 64 phase-3 opportunities, 8 forced-exploration groups give each expert
4 forced updates under the alternating rule; greedy selection may add updates.

For each expert, report all R1/R2 clean accuracies at phase-2 and phase-3 end,
after the first 480 phase-4 examples, and at phase-4 end; local update counts;
and the forced-exploration/greedy-usage split.
In particular, do not omit expert 1's phase-2 R1 accuracy.
The same experts' phase-2 frozen copies are retained as diagnostic references;
no new training is performed, and these do not change the main sparse-A reference points.

Predetermined interpretation branches:
- Consistent with specialization: R2 learning increases in one expert while
  R1 is retained in the other, and system selections use the appropriate expert.
  R2 gains and R1 losses are reported numerically for each expert; usage rates alone are insufficient.
- Consistent with archive-like retention: the expert providing a phase-4 advantage
  received few phase-3 updates, gained little on R2, and retained R1 performance
  close to its own phase-2 copy. This is a routed-archive explanation, distinct
  from specialization that separates learning and retention.
- Mixed/uncertain: if the tables do not distinguish these explanations,
  neither is declared the definitive mechanism. Failure to distinguish an R2
  gain from zero does not prove no learning or complete freezing.

These branches are descriptive diagnostics, not a new success test or a rule
for excluding main conditions. B/D superiority is not automatically called “true specialization.”

## 5. CPR source and experimental adaptation

Source: Luc McCutcheon, Evangelos Chatzaroulas, Saber Fallah,
Calibrated Partial Resets: Preventing Policy Collapse in Continual
Reinforcement Learning, arXiv:2607.24996v1, Section 3, Equations 3/5/6/7 and Appendix A.
Source: https://arxiv.org/html/2607.24996v1
This draft is not an exact reproduction of the paper's RL experiment.

The source includes neuron utility based on the mean per-example gradient
norm of incoming weights; normalization by the layer mean; EMA;
a utility-dependent graded coefficient; periodic partial resets;
moving incoming weights toward the initialization distribution and shrinking
outgoing weights, followed by resetting EMA to 1.
The EMA coefficient, frequency, norm choice, and decisions about biases and
Adam moments below are experiment-specific choices, not assumed to come from the source.

Applied only to the 64 hidden neurons of an expert/base network, not to the router.
At each expert update, using pre-update noisy loss:
S_i = mean of the L2 norms of the incoming-weight gradients within the minibatch.
The norm of the mean gradient is not used. Divide S_i by the layer mean + 10^-8.
Initially u_i = 1; u_i ← 0.99 u_i + 0.01 normalize(S_i).
After every 8 local expert updates, following the Adam step:
r_i = 0.01 × min(2 sigmoid[-4(u_i−1)], 1).
Incoming weight row ← (1−r_i) row + r_i ξ_i.
At each intervention, ξ_i is independently drawn from the base layer's initial uniform distribution.
Outgoing weight column ← (1−r_i) column.
Biases and Adam moments are preserved in this adaptation; they are not additionally reset.
The layer's u values then return to 1.
No full reset, attraction to fixed initial weights, or uniform weight decay is used.

In D, only the updated expert's local clock/EMA advances;
the inactive expert is not pulled toward initialization.
In C, the single network's local clock operates.
Thus 64 global opportunities do not mean 64 steps per expert in D.
CPR and routing operate under the same rules throughout phases 1–2.
Intervention state is not reset at phase-3 start.
The 3125 preparation opportunities and actual warm-up counts per expert are reported separately.
If controls fail, these values are not changed based on main results;
a new protocol version is required.

### Intervention budget and renewal activity

C makes 8 interventions in 64 local updates.
Considering CPR multipliers alone, the coefficient of the old component is
at least 0.99^8 = 0.922745; the maximum multiplicative reduction is about 7.7255%.
For expert j in D, the intervention count is calculated from the phase-start
local counter k and within-phase update count n as
floor((k+n)/8) − floor(k/8); the counter is not assumed to start at zero.
The reduction bound 1−0.99^m is also reported for each expert.

This bound does not mean the total weight-displacement norm is below 7.73%.
Random ξ and intervening Adam steps have different effects.
Zero I alone proves neither “no interaction” nor “renewal is unmeasurable.”

At every CPR intervention, record the difference between POST-Adam/PRE-CPR
weights and POST-CPR weights. For each incoming row and outgoing column:

L_i = sum_k ||w_i,k^after − w_i,k^before||_2 /
      max(||w_i,phase-start||_2, 10^-8).

Report the raw numerator, denominator, within-phase intervention count,
r_i distribution, and row/column medians and quantiles together.
L_i is cumulative intervention path length, not net displacement or behavioral benefit.
Adam-induced change is not included in this numerator.
Rows with zero norm at phase-2 start are flagged separately.

Approved numerical activity check:
In the 40000-example single-regime C and ideal-routed D expert controls,
the median incoming-row L_i over the last 64 local updates must be at least 0.001;
all values must be finite and intervention counts must agree with the clock rule.
This is a cumulative movement threshold equal to 0.1% of the weight norm;
an experimental mechanical lower bound, not a literature-derived efficacy threshold.
Do not proceed to the power pilot unless every mandatory check in the three
control pairs passes. Learnability and other control requirements remain in force.
Report the same diagnostics in the main experiment; small movement does not
exclude a main pair, and hyperparameters are not changed afterward.

## 6. Naive baselines and diagnostics

Sparse-A is identical to A in phases 1–2; in phases 3–4 it takes one Adam step
on groups divisible by 2 or 4, respectively, under the shared global group counter.
Skipped groups are not trained later; optimizer moments and the step counter
do not advance on skipped groups. Predictions are produced for all examples.
Actual phase-3 step counts are 32 and 16; in the first 480 phase-4 examples,
they are 15 and 7. Thus D480 uses the same example window in every condition;
30 actual steps are not claimed for sparse conditions.

Sparse-A-75 branches from A's phase-2 model and optimizer state, like the other
sparse conditions. In phases 3–4, groups whose global index is divisible by 4
are skipped; all other groups receive one Adam step.
Skipped data are not reused; optimizer moments and the step counter do not advance.
Under the 40k/10k/1024/4k schedule, it has 48 actual phase-3 updates and 23
in the first 480 phase-4 examples. If the phase schedule changes, recount using the same calendar.
It is run for every power-pilot and main-experiment pair, but is not added to
the reference envelope, main 2×2, or primary test family.
An intermediate update rate does not guarantee learning accuracy between sparse-A-50 and A.

Frozen-F2 preserves all weights and optimizer state in phases 3–4.
With the same prediction procedure, its damage and D480 against its own reference
are exactly zero. R2 accuracy is measured directly, not assumed equal to teacher agreement.
Replay's own phase-2 frozen copy is also reported as a comparison requiring no further training.

Recent k-NN: Euclidean distance on raw 32-dimensional observations;
last 256 pairs, k=5; voting ties choose the smaller class index;
equal distances prioritize more recent examples.
With insufficient history, use all available examples; with empty history, class0.
Insert after prediction; do not reset the window at phase boundaries.
Use noisy labels; evaluation data do not enter the window.
Replacement of the window in 256 examples does not guarantee high accuracy.

Replay diagnostic: separately track example provenance, time index,
and clean targets for both rules for the evaluator.
True regime is not a learning input.
Report separately the share of sampled clean historical-rule targets disagreeing
with the current clean rule and disagreement due to noise.
Correlations are diagnostic, per seed, in fixed groups of 16 examples;
they are neither causal evidence nor a main 2×2 criterion.
Replay predictions must match exactly with the diagnostic enabled and disabled.

## 7. Measurements and sparse-A reference

### Frozen evaluation: all prediction state is preserved

At each phase end, copy weights, context window, router, experts,
local/global counters, and k-NN memory if present together.
None of these copies is updated during evaluation;
evaluation inputs or labels are not added to history.
Test order must not change the result.

For B/D, use the actual phase-end 132-dimensional context.
Select the router's highest-scoring expert in that context; ties choose the smaller index.
Forced exploration is disabled in frozen measurement; expert selection is fixed across the test.
This measures a greedy frozen policy, distinct from the online system with exploration.
Ideal expert selection is an additional diagnostic only, not a replacement for actual system accuracy.
A+context combines each test input with the same fixed phase-end context.
k-NN predicts using the actual last-256 memory at phase end;
filling memory with test examples or warming it with true-rule labels is prohibited.

For the same test inputs, compare a prediction vector generated once against
both R1 and R2 clean targets in the evaluator.
Do not prepare different contexts per rule.
Thus evaluating the phase-3 model on R1 does not become renewed R1 learning
or provision of R1 identity to the router.
Expert–rule mapping calibration likewise does not alter expert weights or context.

D480's phase-2 frozen reference also copies the entire phase-2 prediction state.
Exploration is disabled in the B/D reference and enabled in the phase-4 online
system as specified; explicitly report that the difference includes this policy distinction.
The Frozen-F2 baseline is a context-free A copy; the exact-zero damage and D480
check against its own reference applies to this condition.

Secondary D480 excluding exploration groups:
Remove groups falling on the global exploration calendar within the first
480 phase-4 examples. Apply the same calendar mask to all conditions;
pair the remaining examples' online errors with that method's phase-2 frozen-reference errors.
Report the remaining example count, total difference, and per-example difference
together; do not divide by 480. With no remaining examples, the metric is undefined.
Starting the group counter at 1, the current 40k/10k/1024 schedule has phase-4
global groups 3190–3219: 3192, 3200, 3208, and 3216 are exploration groups.
Thus 64 examples are excluded and 416 remain.
For a changed phase schedule, recompute the mask under the same global rule;
these counts are not assumed fixed.
This analysis does not remove the effect of earlier exploration updates on the model;
it is not the counterfactual outcome of training without exploration.
Primary D480 and I continue to use all 480 examples.

For each method/pair, publish R1 and R2 accuracies on the same independent
20000 M2 inputs at phase-2/3/4 end, and on a copy taken immediately after
completion of the group update, any CPR intervention, and history/memory update
at the 480th phase-4 example. Publish damage, recovery, and absolute accuracies.
Also report D480 and D480/480, total/per-example oracle regret per phase,
actual steps, processed examples, memory, and time.

Primary plane:
x = frozen R2 accuracy at phase-3 end (learning).
y = frozen R1 accuracy after processing 480 phase-4 examples (early return).
Both axes are measured on the same independent evaluation inputs with all
prediction state frozen. y measures recovery, not retention before relearning.
Phase-3-end R1 is the second mandatory plane; phase-4-end R1 is auxiliary.
D480 is a separate online cost and is not redefined.

The reference consists of four points: Frozen-F2, sparse-A-25, sparse-A-50, and A.
For each pair, calculate x_min and x_max from these four points;
do not assume A supplies x_max.
Among references at the same x_max, choose the highest y, called y_right.
A's own coordinates are also published.
F_i(x) is the upper concave envelope: the largest y among nonnegative reference
mixtures summing to 1 whose mean x equals the requested value exactly.
This is a reporting reference, not a newly trained method.

For B and D, assign each pair to one of the following disjoint categories:
- Within support S: x_min ≤ x_m < x_max. G_i = y_m − F_i(x_m).
- Right side R: x_m ≥ x_max. P_i=1 only if y_m ≥ y_right and at least one
  coordinate is strictly better; otherwise P_i=0.
  Exact coordinate equality is the “equal” subcategory; higher learning but
  lower y is the “trade-off” subcategory. G is undefined for a trade-off.
- Left side L: x_m < x_min. G and Pareto-success evaluation are undefined.
If all reference x values are equal, S is empty and the R rule still applies.
Decisions use unrounded correct-prediction counts with the same evaluation size;
boundaries are not moved using tolerances.
On the right, only Pareto dominance over the endpoint reference is measured;
this is not a claim of dominating the entire reference envelope. No extrapolation.

Two separate conditional primary components:
1. Mean G among S pairs. The practical-superiority boundary is 0.02.
2. Pareto-dominance rate sum(P_i)/n_R among R pairs.
   The denominator includes all R pairs, including equality and trade-offs,
   not just successful pairs.
For each method, publish n_S, n_R, n_L, and right-side subcategories together with N.
Subgroups are defined by realized outcomes; inference is conditional on these
subgroups, not superiority across the entire generator population.
G and P are not combined into one score; left/trade-off pairs are not assigned zero G.

Approved decision thresholds: with at least 10 pairs in the relevant subgroup,
report “practical superiority within support” when the one-sided 98.75%
bootstrap lower bound for G exceeds 0.02; report “majority Pareto dominance
on the right” when the one-sided 98.75% Clopper–Pearson lower bound for P exceeds 0.50.
B/D × two components = four claims, with Bonferroni total alpha 0.05.
For an empty subgroup or one smaller than 10, do not conclude the corresponding
claim; the other component is not canceled.
Use an exact binomial interval even when P is entirely 1 or 0;
do not use a zero-width bootstrap interval.
These thresholds are approved design choices, not thresholds mandated by the literature.

Positions of C and the other conditions are diagnostic.
Out-of-support observations do not cancel the whole analysis;
retain all pairs in the report and I analysis.
A positive result for one component does not conceal a trade-off in the other.
This rule does not guarantee outperforming A+context or k-NN;
general architectural superiority must also consider those competitors' results.

### Empirical calibration with Sparse-A-75

The four reference points remain unchanged: Frozen-F2, sparse-A-25,
sparse-A-50, and A. Sparse-A-75 does not participate in constructing the envelope.
Use the same frozen x/y axes and S/R/L classification.

Within S, calculate G75_i = y75_i − F_i(x75_i).
Report signed mean G75, mean |G75|, per-pair values, and n_S75/n_R75/n_L75 together;
right and left observations are not assigned zero G.
Within R, calculate the P75 rate using the same strict dominance rule:
the denominator includes every R75 pair, including equality and trade-offs.
If R75 is empty, the rate is undefined.
Report the rate and denominator descriptively; no new test is added to B/D's primary alpha family.

G75 is not theoretically zero.
Curvature of the four-point interpolation and finite training/evaluation
variability may contribute together.
If the signed mean is far from zero, examine a systematic envelope-deviation explanation;
if the signed mean is small but the absolute mean large, examine
sign-changing deviation/noise explanations.
These patterns do not definitively separate causes; opposing systematic
deviations can also cancel in the mean.
G75 is an empirical sensitivity diagnostic, not proof of B/D's true null distribution.

Approved stopping rule for the power pilot:
- Among 12 pairs, there must be at least 6 within-support Sparse-A-75 pairs.
  Fewer means insufficient calibration; the main experiment does not start.
- If mean |G75| ≥ 0.015 among those within-support pairs, the main experiment does not start.
  Compare unrounded numbers; equality also triggers stopping.
- 0.015 is a preselected caution margin for the primary 0.02 threshold,
  not a decomposition asserting that exactly 75% of superiority is error.
- On failure, do not automatically increase or decrease the threshold.
  Preserve power-pilot findings; a justified new preregistration revision
  and user approval are required. Rewrite the power plan for any changed success boundary.
- Passing calibration does not show small interpolation error in every pair
  or validate the null distribution for B/D.

In the main experiment, G75/P75 are reported only;
main results do not change the threshold, N, or method,
and the experiment is not terminated by a retrospectively chosen stopping rule.
Primary interpretations state the limitation if calibration deviations are large.

For P, the 0.50 boundary may be conservative when B≈A because of conditioning
on R and the learning–retention trade-off.
This conservatism is not a mathematical guarantee.
The P75 rate within R75 provides an empirical comparison;
it is not identified with B/D's null rate and does not automatically change the 0.50 boundary.

## 8. Interaction and power

E_i,m = D480_i,m / 480.
I_i = (E_i,D − E_i,B) − (E_i,C − E_i,A).
Negative I means renewal produces relatively greater additional-error reduction
under routing. Each E uses its own phase-2 reference;
I is not purely mechanical reuse or a capacity-adjusted effect.
Do not interpret I without phase-3 R2 and absolute R1 measurements.

Existing A/replay data do not supply I variance; no power has been calculated.
After controls pass, conduct a power pilot of all conditions, including
Sparse-A-75, on 12 paired runs separate from the main experiment.
It is not run in this round.
Before locking main N/seeds, the Sparse-A-75 calibration requirements in
Section 7 must pass; otherwise do not proceed to the main experiment.
Target interaction magnitude |I|=0.05; two-sided alpha 0.05, target power 80%.
Using the pilot's pair-level I standard deviation s, plan:

N_I = ceil(((1.96+0.842) × 1.25s / 0.05)^2).

The 1.25 coefficient is a caution margin for a small pilot, not an exact power guarantee.
Primary inference now concerns two different subgroup parameters;
discarding right/left pairs and treating within-support variance as population variance is prohibited.
The revision-0 rule stopping the power process at a single out-of-support pair has been removed.

For G, target true difference 0.05, boundary 0.02;
use z=2.2414 for one-sided alpha 0.0125.
If the pilot's relevant S subgroup has at least 6 pairs and a positive standard deviation,
the required conditional count is:

n_G = max(10, ceil(((2.2414+0.842) × 1.25s_G / 0.03)^2)).

Otherwise report that power for G “could not be calculated”;
do not produce a low N from zero variance.
Planning for the other component and I continues.

For P, the approved target true dominance rate is 0.80 and null hypothesis 0.50.
n_P is the smallest n≥10 for which the following exact binomial test has at least 80% power:
the critical value is the smallest success count whose upper-tail probability
under p=0.50 is ≤0.0125; power is the probability of reaching this critical
value under p=0.80.
Do not change this target based on the pilot's observed dominance rate.

For each B/D method, calculate one-sided 80% Clopper–Pearson lower bounds
q_S and q_R for the pilot's S and R occurrence rates.
If a G plan can be calculated and q_S>0, the total pair requirement is the
smallest N with probability ≥90% of obtaining at least n_G S pairs under Binom(N,q_S).
For R, perform the same calculation using n_P and q_R.
For an unobserved subgroup, report that the requirement is unknown;
do not claim that it will not occur in the main experiment or that it has sufficient power.

Main N is the maximum of 20, N_I, and all calculable B/D subgroup requirements.
If calculated N>100, the budget is insufficient; the main run does not start.
If neither component's power plan can be calculated for B or for D,
the main run does not start; a new protocol revision is required for the definition/sampling plan.
The process also stops if I variance is zero or nonfinite.
Before main results are seen, disclose which components could be planned;
do not declare adequate power for an uncalculable component.
If the relevant main-experiment subgroup has fewer than 10 pairs, do not conclude
that claim; do not add pairs afterward.
The subgroup-count plan is an approximate conditional power plan under the
target effect, not a guarantee of joint or realized 80% power.

Write main N and the complete seed list in an additional lock record before seeing main results.
No early stopping or increase in N based on interim results.

Main inference: resample independent pair indices with replacement 10000 times;
apply the same indices to all methods, both axes, and the reference points.
Each replicate carries the pair's own envelope and category membership together;
calculate mean G among that replicate's S pairs.
Averaging all pairs' points first and constructing a single envelope is a
different metric and is not used.
G is undefined in replicates without S; publish the empty-replicate fraction.
Compute a conditional percentile interval from nonempty replicates;
if the empty fraction exceeds 1%, do not conclude G inference.
Primary inference for the R rate is the exact binomial interval above;
bootstrap is auxiliary only.
For I, report the pair-level mean and two-sided 95% percentile interval;
interaction in this draft is secondary, outside the confirmatory family.
The 480 time steps or overlapping context rows are not independent repetitions.
If a conditional bootstrap over evaluation examples is provided, label it
secondary; it does not replace training/generator variance.
The power pilot is excluded from the main bootstrap sample.

## 9. Prerequisites and stopping rules

Stages: protocol approval → generator acceptance → single-regime controls/gate →
filtered-duration pilot if needed → power pilot → N/seed lock → main experiment.
Writing this document does not mean these stages have passed.

v0.4 candidate: normalized margin threshold 0.25, requiring both rules together;
normalization on 20000 independent unfiltered examples from an equal M1/M2 mixture;
offsets are not readjusted. Separate M1/M2 exclusion ceilings of 30%.
At acceptance, every class in all four mixture/rule slices must have share 18–35%;
disagreement must be 40–70% in both mixtures.
Candidates are considered sequentially, at most 200.
Exclusion and acceptance are not measured on the same training data.
Per candidate, exclusion uses 100000 proposals per mixture;
balance/disagreement uses 20000 accepted examples per mixture.
Reject a candidate if the 1000000-proposal budget is exceeded in either mixture.
Rejection of one candidate does not automatically reject the entire version;
stop if insufficient suitable generators are found by the limit.
Do not change bands or offsets.

Gate: single-regime controls of the base network on R1/M1 and R2/M2;
each has 40000 noisy training examples, an independent 20000-example
threshold calibration, and 20000 clean test examples.
Threshold = majority + 0.9 × (1−majority); the Wilson lower bound must exceed it.
Also provide C's same control and D expert controls with ideal expert selection.
No power pilot until all mandatory checks pass in three separate control pairs.
If C/D controls fail, do not change main model settings; a version revision is required.

Router control: independent training/test streams to distinguish R1/R2 on the
same inputs; clearly label this as a diagnostic supervised with regime identity.
Control weights are not transferred to the main router.
This diagnostic tests representation sufficiency, not actual online routing.
For actual online B/D, a separate pilot examines expert usage counts,
counterfactual loss, the ideal-routing gap, and specialization tables.
Control success criteria: at least 90% balanced regime accuracy on independent
diagnostic blocks; at most 2 percentage points of B/D single-regime end-to-end
clean accuracy loss relative to the same-expert reference.
These thresholds are approved design choices.
No remapping that conceals expert starvation or collapsed usage.

If v0.4 passes the gate, test phase-3 candidates 1024/1536 on three separate
pilot pairs while retaining 40k/10k preparation and 4k recovery.
Require A phase-2 accuracy ≥86% and damage of 20–40 points in all three pairs;
choose the shortest suitable candidate.
If neither qualifies, a new version is required; no automatic candidate search.
The v0.3 choice does not validate the filtering effect.
Gate failure may require questioning the gate definition, but does not mean
the gate is definitely the problem. The formula changes only through a new preregistration.

## 10. Separate data partitions, resources, and records

Controls, duration pilot, power pilot, and main experiment use different
generator candidate pools and different training/evaluation streams.
Teacher pool starting points are 10000/20000/30000/40000, respectively.
In each section, consider at most 200 candidates in increasing order and take
the first suitable ones: 3 distinct generators for controls, 3 for duration,
12 for power, and N for the main experiment.
Generators are not selected based on student performance.
Each main pair has a different initialization/training seed;
methods within a pair share data and pairable initializations.
Main failed conditions are not excluded or replaced based on performance.

Randomness root seed: 20260916; derive hierarchical independent streams from
section, pair, role, phase, expert, and replicate indices.
Labeled roles: teacher, offset, scale, acceptance, exclusion, model0, model1,
training, CPR, reservoir replacement, reservoir sampling, mapping, evaluation,
power calculation, bootstrap.
Derived numerical seeds are written in the lock manifest.
If the existing generator's implicit offset seed is replaced with an explicit
role seed, record this as a data-generation version; do not assume bit equality to earlier results.

In every training run, save the model, optimizer, router, utility EMA, local
clocks, buffers, and RNG states; inputs, latent examples, clean/noisy targets,
online predictions, routing decisions, and all frozen predictions.
Take checkpoints at phase ends and at intervals of 16 examples during the
first 480 examples of phases 3/4.
Test record reloading and forward-prediction equality. Do not overwrite files.
Archive protocol, source, environment, seeds, and file hashes before the run.

Report parameters, active/total expert counts, additional gradient cost,
optimizer steps, training-example counts, memory, and time separately.
Include CPR per-example gradients and two-expert loss computations in cost.
Because capacity/computation are not equalized, system-level differences are
not presented as pure structural contributions.
An equal-budget claim requires a new control.
Stop on numerical error or record mismatch; reproduction with the same seed
is allowed only after a documented software correction. Preserve both versions.

## 11. Approval and locking

Revision 1 was approved by the user on 2026-09-16.
This version includes the within-support/Pareto distinction, two frozen axes,
expert/archive diagnostics, the CPR activity check, and exploration-masked secondary cost.
Final approval added the Sparse-A-75 calibration diagnostic, at least 6
within-support pilot pairs, and stopping when mean |G75| ≥0.015.

Approved numerical choices:
- Right-side conditional dominance-rate boundary 0.50; power target 0.80.
- At least 10 main pairs per component; at least 6 pilot S pairs for G variance.
- Alpha 0.0125 for each of four primary claims.
- Median L_i ≥0.001 over the last 64 local steps in the CPR control.
- The subgroup power plan and uncalculable-component policy in Section 8.
- The Sparse-A-75 calibration stopping rule in Section 7.
No superiority claim without reporting support and category counts.

Record the content lock by taking SHA-256 over the final bytes of this file
and keeping a separately dated lock record.
Verify the Git commit identity separately; do not backdate a hash or commit timestamp.
A local Git record is not an independent preregistration repository or a
trusted third-party timestamp.
The historical draft filename is retained; the heading and lock record identify the version.

After locking, the only tasks in this round are the dated record and first Git commit.
Do not start implementation, training, generator acceptance, or the power pilot.
In future, no data-producing run starts before implementation tests are
audited for protocol compliance.
After the power and duration pilots, permitted additional locks within revision 1
are the N/seed list and duration selected by the written rule.
If G75 calibration requires changing the threshold, this is not a permitted
silent addition; it requires a new revision and renewed approval. Preserve revision 1.