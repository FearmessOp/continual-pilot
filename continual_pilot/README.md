# Continual learning — project guide and closed research archive

**Final status: research line closed on 2026-09-16.**
No new threshold, candidate pool, scientific revision, or training run is planned.

This is an English publication guide, not a full translation of the historical
research log. The [Turkish original](README.tr.md) is preserved byte-for-byte,
including historical results, instructions, and interpretations later qualified
or withdrawn. Its “current status” and “next step” headings do not override
the final closure.

## Purpose and experimental setting

The project investigated whether routing and renewal together could improve
the learning–retention trade-off beyond simply updating less often.

The synthetic task has four classes and eight latent factors embedded without
observation noise into 32 observed dimensions. The four-phase schedule is
M1/R1 → M2/R1 → M2/R2 → M2/R1: first a mixture shift, then a rule change,
then a return to the previous rule under the same mixture.

The final base learner is 32→64→4, with ReLU, Adam at a fixed learning rate
of 0.001, and minibatches of 16 new examples. A/C receive only the current
32-dimensional observation. B/D use two such experts and a causal router
taking a 132-dimensional summary of the last 64 noisy-label observations.
The summary comprises four class frequencies and four class-conditioned
32-dimensional means. Current labels, clean labels, and true regime identities
are not supplied to the learned online policy.

The principal planned family was A (base), B (routing), C (CPR renewal),
and D (routing plus CPR). CPR means **Calibrated Partial Resets**; the
supervised adaptation here is not a reproduction of the source paper's
reinforcement-learning experiments. The comprehensive protocol also specifies
replay, frozen and sparse-update baselines, recent k-NN, and context diagnostics.
Their inclusion in a protocol does not mean the main comparison was executed.

## Final gate results

v0.4 accepted **0 of 200** generator candidates.
The final v0.5 attempt changed the normalized margin threshold to **0.1**
and used a new pool, while retaining the **30%** exclusion ceiling,
**18–35%** class-share band, and **40–70%** disagreement band.
Teachers **11002, 11003, and 11004** were accepted among the first five candidates.

Only pair 0, teacher 11002, underwent the first stationary R1/M1 condition.
Each of its six unique runs received the same **40000** noisy training
examples; threshold calibration and frozen evaluation each used a separate
**20000** examples. The measured threshold was **93.2525%**.

| Run | Clean accuracy (%) | 95% Wilson interval (%) | Outcome |
|---|---:|---|---|
| A | 92.835 | [92.469272; 93.184276] | Failed gate |
| C | 90.990 | [90.585262; 91.378994] | Failed gate |
| A expert-1 reference | 92.880 | [92.515301; 93.228230] | Below threshold; diagnostic |
| C expert-1 reference | 90.875 | [90.468013; 91.266287] | Failed gate |
| B | 92.790 | [92.423247; 93.140318] | Below threshold; additional comparison |
| D | 90.910 | [90.503696; 91.300591] | Below threshold; additional comparison |

The lower Wilson bound had to strictly exceed the threshold.
A's upper bound was below it; closeness was not counted as success.
Intervals are conditional on the trained model and do not include
training-seed variation or calibration-threshold uncertainty.

CPR movement checks passed. B/D also passed the requirement of losing at
most **2 percentage points** relative to their A/C references.
Neither result establishes absolute learnability. Expert-1 references did
not replace primary references, and C was not retrained as D's reference.

R2/M2 stationary training, the other pairs, the representation diagnostic,
duration and power pilots, and the main factorial experiment were **not run**.
The **113** passing mechanical tests are not evidence that the scientific gate passed.

## Evidence and lessons

- [Final results and lessons — English](line2/FINAL_RESULTS_AND_LESSONS.en.md)
  ([Turkish original](line2/FINAL_RESULTS_AND_LESSONS.md)).
- [Non-normative comprehensive protocol translation](line2/PREREGISTRATION.en.md).
- [Authoritative locked Turkish protocol](line2/PREREGISTRATION_DRAFT.md).
- [Final v0.5 preregistration](line2/PREREGISTRATION_V05_2026-09-16.md)
  and [content lock](line2/LOCK_V05_2026-09-16.md).
- [Source-bound mechanical validation evidence](line2/validation_v05_2026-09-16_01.json).
- [Post-v0.4 design lesson](line2/LESSONS_ACCEPTANCE_2026-09-16.md).
- [Preserved historical exploration log](README.tr.md).

Linked design parameters must be checked jointly before locking them.
Generator acceptance is not learnability, mechanical movement is not
behavioral benefit, and a small relative loss is not absolute success.
Full-state records support reproducibility; aggregate accuracy alone cannot
establish historical prediction-vector equality.

Earlier v0.3 A/replay studies were **exploration, not hypothesis tests**:
the learnability gate had not passed. Their selected **40000/10000/1024/4000**
phase schedule belonged to that exploration and was not automatically
validated for the filtered task. Low transition cost alone does not establish
superiority when new-rule learning is weaker.

## Environment and historical execution instructions

Recorded experiments used CPU execution with Python **3.13.2**, NumPy
**2.2.6**, and PyTorch **2.7.1**; the final runtime identifies the PyTorch
build as **2.7.1+cu118**. A GPU was not used. Source inventories, exact
runtime details, seeds, and configuration are in the run records.

The [historical execution section](README.tr.md:877) retains the original
commands for tests, a short end-to-end run, reproduction, and command-line help.
Those commands were written for earlier stages. Some can train models or
overwrite output directories, and older entry points do not all implement
the later full-state recording policy. They are archival instructions,
**not authorization to resume the closed research line**.

To inspect the published work without training, read the linked reports and
download the [release assets](https://github.com/FearmessOp/continual-pilot/releases).
The [v0.4 backup record](line2/BACKUP_V04_VERIFICATION_2026-09-16.json)
and [v0.5 backup record](line2/BACKUP_V05_VERIFICATION_2026-09-16.json)
describe archive hashes and complete member verification. Preserve the
archives and do not load untrusted serialized objects with unrestricted pickle.

## Timestamp, privacy, and future-work boundary

The [original protocol attestation](line2/OTS_VERIFICATION_2026-09-16.json)
was verified at Bitcoin block **967295**. Merkle commitment, header hash,
and declared-target proof of work were checked locally; chain placement was
cross-checked using two HTTPS explorers. This was not full-node validation.
The attestation does not timestamp v0.5 or an English translation.

Authoritative Turkish protocol SHA-256:

0800b0647a0feec22dc13b83ddfaaa7478dc4cd8fe54d3a923423f3cd8d136f7

[Privacy maintenance](line2/PRIVACY_AUDIT_2026-09-16.md) cleaned advertised
history while preserving the real author name. Old commits remained accessible
by object ID on GitHub at verification; complete server-side erasure is not claimed.

**Future work — unexecuted scope:** filtered-duration validation, the power
pilot, and the main factorial experiment in the preserved comprehensive
protocol. This label is neither permission nor a commitment to continue.
The failure did not prove or disprove the main routing–renewal hypothesis:
its planned test was never reached.

License: [MIT](../LICENSE).