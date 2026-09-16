# Results and lessons — research line closed

English translation of the [Turkish original](FINAL_RESULTS_AND_LESSONS.md).
Historical commit IDs below are retained as provenance; see the
[privacy audit](PRIVACY_AUDIT_2026-09-16.md) for the subsequent history rewrite.

Date: 2026-09-16.
**Status: the final v0.5 attempt is complete; no new scientific runs will be conducted.**

## Summary

v0.5 passed generator acceptance, but the first control pair failed the R1/M1
learnability gate. The owner's firm closure rule, specified before the results,
was applied. No other threshold, pool, training setting, or scientific revision
was tried.

This work neither proved nor disproved an advantage of routing and renewal
in continual learning: the main experiment addressing that question was never
reached. The result is a control failure under a fixed budget and preregistered gate.

## 1. Acceptance

Single threshold τ = 0.1; exclusion ceiling 30% for each mixture.
Class-share band 18–35%; disagreement band 40–70%.
Offsets were not changed after filtering.

| Teacher | M1 exclusion (%) | M2 exclusion (%) | Decision |
|---|---:|---:|---|
| 11000 | 27.577 | 27.612 | Rejected for balance |
| 11001 | 23.615 | 21.065 | Rejected for M2 balance |
| 11002 | 23.352 | 22.305 | Accepted; pair 0 |
| 11003 | 17.526 | 16.732 | Accepted; pair 1 |
| 11004 | 21.435 | 21.301 | Accepted; pair 2 |

Search stopped when the first three suitable generators were found:
5 candidates, 3 accepted, 2 rejected. The remaining 195 candidates were not
examined. No candidate was rejected for exclusion, disagreement, or proposal budget.

Across the five candidates, median exclusion was 23.352% for M1 and 21.301%
for M2. These are on the same scale as the approximate 22.9% expectation;
the flag for exceeding 28% was not triggered in either mixture.
This does not validate independence or an offset effect. A population acceptance
rate is not inferred from this small sample stopped at the first three acceptances.

Full record: [acceptance summary](results_control_v05_01/acceptance_summary.json).

## 2. Executed gate: only pair 0, teacher 11002, R1/M1

Each unique run received the same 40000 noisy examples.
Threshold calibration and frozen testing each used a separate 20000 examples.
Calibration class counts: 5146, 6505, 4370, 3979.

Majority = 0.32525.
**Measured threshold = 0.32525 + 0.9 × (1 − 0.32525) = 0.932525.**
Passing requires the 95% Wilson lower bound to strictly exceed this threshold.

| Condition | Clean accuracy (%) | 95% Wilson interval (%) | Gate comparison |
|---|---:|---|---|
| A, expert-0 initialization | 92.835 | [92.469272; 93.184276] | Did not pass |
| C, expert-0 initialization | 90.990 | [90.585262; 91.378994] | Did not pass |
| A, expert-1 reference | 92.880 | [92.515301; 93.228230] | Did not pass; diagnostic |
| C, expert-1 reference | 90.875 | [90.468013; 91.266287] | Did not pass |
| B system | 92.790 | [92.423247; 93.140318] | Below threshold; additional comparison |
| D system | 90.910 | [90.503696; 91.300591] | Below threshold; additional comparison |

A's point accuracy is 0.4175 percentage points below the threshold;
its Wilson upper bound is also below it. Closeness was not counted as passing.
The intervals are conditional on the trained model; they do not cover
training-seed variability or threshold-calibration uncertainty.
The expert-1 reference was not substituted for A.

As preregistered, the six unique runs of the first stationary condition were
completed for the diagnostic table. Mandatory failure stopped progression to
the next condition. C was not retrained for D's primary single-network reference.

## 3. CPR movement and B/D system checks

| Check | Measurement | Decision |
|---|---:|---|
| C incoming rows, last-64-step median L | 0.1010321379 | ≥0.001; passed |
| Expert-1 CPR reference median L | 0.1011665240 | ≥0.001; passed |
| A minus B clean accuracy loss | 0.045 percentage points | ≤2 points; passed |
| C minus D clean accuracy loss | 0.080 percentage points | ≤2 points; passed |

Both isolated CPR controls recorded 8 interventions in the last 64 local steps,
finite values, and agreement with the clock rule.
L is cumulative intervention path length divided by the phase-start norm;
it is not net weight displacement or behavioral benefit.
The C record was also used for the isolated ideal-D expert-0 control;
these are not independent repetitions.

The usage table is identical for B and D:

| Expert | Local updates | Forced exploration | Greedy usage |
|---|---:|---:|---:|
| 0 | 2343 | 156 | 2187 |
| 1 | 157 | 156 | 1 |

The B experts' R1 accuracies were 92.790% and 88.025%;
the D experts' were 90.910% and 87.655%.
Usage concentrated on expert 0 in this single stationary regime.
This observation does not prove rule specialization, archiving, or a
continual-learning advantage. Usage counts alone cannot causally separate
the costs of routing and splitting updates.

## 4. Confusion matrices and learning curves

Rows are true classes and columns predicted classes, ordered 0–3.

| Condition | True class 0 row | True class 1 row | True class 2 row | True class 3 row |
|---|---|---|---|---|
| A | 4507,142,147,227 | 89,6259,132,75 | 90,75,4197,8 | 264,127,57,3604 |
| C | 4401,168,224,230 | 136,6158,202,59 | 104,138,4113,15 | 321,123,82,3526 |
| A expert-1 | 4502,142,144,235 | 93,6261,128,73 | 87,72,4203,8 | 266,120,56,3610 |
| C expert-1 | 4379,170,237,237 | 132,6154,205,64 | 98,132,4126,14 | 322,135,79,3516 |
| B | 4547,138,119,219 | 96,6258,121,80 | 112,77,4173,8 | 290,127,55,3580 |
| D | 4452,157,198,216 | 146,6157,194,58 | 129,151,4078,12 | 341,130,86,3495 |

| Condition | First 1000 online clean (%) | Last 1000 online clean (%) |
|---|---:|---:|
| A | 60.3 | 93.6 |
| C | 60.3 | 91.4 |
| A expert-1 | 62.8 | 93.5 |
| C expert-1 | 62.9 | 90.8 |
| B | 58.6 | 93.3 |
| D | 58.5 | 91.4 |

The complete 40-block curves, class recalls, and measurements of each expert
against both rules are in the
[control report](results_control_v05_01/controls/pair0/condition0/condition_summary.json).
Online block averages do not replace frozen gate accuracy.
The final block does not establish convergence or guarantee success with longer training.

## 5. Not run

R2/M2 stationary training, pair 1 and pair 2 controls, the representation
diagnostic, and its ≥90% success check were not run.
**There is no representation-diagnostic accuracy; earlier probe values were not carried over.**
Diagnostic evaluation of R1-trained networks against R2 labels on the same M1
inputs is not the R2/M2 learnability gate.

The duration pilot, power pilot, main experiment, sparse-envelope superiority
tests, and routing×renewal interaction inference were not performed.
The failure is conditional on the first control pair actually executed;
failure on other teachers is not claimed.

## 6. Time, computation, and records

- Acceptance: 13.4702069 seconds.
- First stationary condition, including recording and evaluation: 93.8466542 seconds.
- Runner wall time: 111.2644011 seconds; approximately 1 minute 51 seconds.
  Startup and final manifest operations may fall outside this measurement.
- Training loops: A 6.330; C 13.426; A expert-1 7.205;
  C expert-1 12.159; B 14.941; D 17.526 seconds.
- Across six runs, 240000 example presentations: reuse of 40000 shared inputs
  across methods, not a count of independent data.
- Each condition had 2500 expert updates; B/D additionally had 2500 router steps.
- C, C expert-1, and D together performed 120000 per-example CPR gradient computations.
- CPU was used. Energy, monetary CPU cost, and process peak memory were not measured.
  The interface's cumulative API charge is not the experiment cost.
- SHA-256 values and sizes of 209 files were reverified against the manifest.
  Total excluding the manifest: 192751253 bytes; largest file: 7838555 bytes.
- [Manifest](results_control_v05_01/manifest.json) SHA-256:
  143f42ef5c780559cfe0a07eb1a8c46cf77cd89fed43633c18be16ac4ce435a4
- [Execution record](results_control_v05_01/execution.json).
- [v0.5 test evidence](validation_v05_2026-09-16_01.json):
  113 mechanical tests passed. Test success is not scientific gate success.

## 7. Lessons

1. **Coupled design parameters must be checked jointly.**
   In v0.4, the margin threshold and exclusion ceiling had been chosen as
   individually reasonable numbers; no candidate was accepted in 200 attempts.
   Failure in a finite pool is not mathematical impossibility.
2. **Generator acceptance is not learnability.**
   Although v0.5 resolved acceptance, the fixed network/budget did not pass the gate.
   Old/new accuracy differences across different teachers and distributions
   are not the isolated causal effect of filtering.
3. **Mechanical movement is not behavioral benefit.**
   CPR movement was measured, but C was 1.845 points below A in this condition.
   This single pair is not evidence of general CPR harm or continual-learning failure.
4. **A relative-loss check is not absolute success.**
   B/D were close to their single-network references; the references themselves
   did not pass the gate.
5. **Records must support the level of the claim.**
   Full reproducibility cannot be claimed without retaining weights, optimizers,
   local clocks, memory, RNG, and example order.
   The historical prediction-equality claim in the earlier margin report is not
   established when the original prediction vector is absent.
6. **Preregistration is stopping discipline, not just a threshold.**
   No new setting was tried after the failure was observed.
   An honest feasibility limit was reported instead of a completed main experiment.

Strong historical statements about complete forgetting, definite causes,
zero acceptance probability, or necessarily vanishing interaction must not be
read as current conclusions. The observations alone do not support those claims.

## 8. Archive and future-work label

The [v0.4 external raw backup](BACKUP_V04_VERIFICATION_2026-09-16.json)
was verified by downloading 11 GitHub release assets and checking 3651 files,
including the manifest. Raw data were not added to Git history.

The [original protocol's Bitcoin attestation](OTS_VERIFICATION_2026-09-16.json)
was verified at block 967295. Proof-of-work/Merkle checks were local;
chain placement was checked through two HTTPS explorers, not full-node validation.
This receipt is not presented as a timestamp for the v0.5 document.

The [locked comprehensive protocol](PREREGISTRATION_DRAFT.md) is preserved.
**Future work — unexecuted scope:** filtered-duration validation, the power
pilot, and the main factorial experiment. This label is not a decision to
continue or permission to rerun. Closure is not reopened depending on the results.

Preregistration: [v0.5 final attempt](PREREGISTRATION_V05_2026-09-16.md).
Historical lock commit: 721aa62c7c1aa6b589f9b051caf7a2f15c74d717.
Historical run-source commit: b3f43f8f25d36796ccaff64676e4e98c70092057.