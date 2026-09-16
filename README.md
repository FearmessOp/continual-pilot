# Continual learning pilot — closed research archive

[Original Turkish README](README.tr.md)

**16 September 2026: The final v0.5 attempt is complete and this research line is closed.**

This repository preserves the design, exploratory pilots, preregistrations,
and failed feasibility checks of synthetic continual-learning experiments.
It does not demonstrate an advantage of routing and renewal in continual
learning. The planned main factorial experiment was not run.

## Final outcome

- **v0.4:** None of 200 candidates passed generator acceptance.
- **v0.5:** With a normalized margin threshold of 0.1, three generators
  were accepted among the first five candidates.
- In the first pair's R1/M1 control, A achieved **92.835% clean accuracy**,
  with a **95% Wilson interval of [92.4693%, 93.1843%]**.
  The required threshold was **93.2525%**, so the learnability gate failed.
- CPR movement checks and the checks requiring B/D to lose no more than
  2 percentage points relative to their single-network references passed.
  These are not evidence of successful absolute learnability.
- R2/M2 training, the remaining pairs, the representation diagnostic,
  duration/power pilots, and the main experiment were not run under the
  stopping rule.
- No further threshold, candidate pool, or scientific revision will be tried.

## Reading guide

1. [Final results, tables, and lessons — English](continual_pilot/line2/FINAL_RESULTS_AND_LESSONS.en.md)
   ([Turkish original](continual_pilot/line2/FINAL_RESULTS_AND_LESSONS.md)).
2. [Final-attempt v0.5 preregistration — Turkish](continual_pilot/line2/PREREGISTRATION_V05_2026-09-16.md).
3. [v0.5 content lock](continual_pilot/line2/LOCK_V05_2026-09-16.md).
4. [Source-bound evidence for 113 mechanical tests](continual_pilot/line2/validation_v05_2026-09-16_01.json).
5. [Project guide](continual_pilot/README.md) and
   [preserved Turkish research log](continual_pilot/README.tr.md).
6. [Non-normative English translation of the comprehensive protocol](continual_pilot/line2/PREREGISTRATION.en.md).

**Future work — unexecuted scope:** the filtered-duration validation,
power pilot, and main experiment in the
[locked comprehensive protocol](continual_pilot/line2/PREREGISTRATION_DRAFT.md).
This label is neither permission to resume nor a commitment to continue.

## Records and limitations

[Raw archives are release assets](https://github.com/FearmessOp/continual-pilot/releases);
large raw archives are not stored in Git history.
The [v0.4 external backup](continual_pilot/line2/BACKUP_V04_VERIFICATION_2026-09-16.json)
was verified after downloading 11 volumes containing 3651 files, including
the manifest. The [v0.5 backup verification](continual_pilot/line2/BACKUP_V05_VERIFICATION_2026-09-16.json)
records the final attempt's external archive checks.

The [original protocol's Bitcoin attestation](continual_pilot/line2/OTS_VERIFICATION_2026-09-16.json)
was verified at block **967295**, using Merkle commitment, header and
proof-of-work checks, with chain placement cross-checked through two HTTPS
explorers. This was not local full-chain validation. It does not timestamp
the v0.5 document or any English translation.

The locked Turkish protocol remains authoritative. Its SHA-256 is:

0800b0647a0feec22dc13b83ddfaaa7478dc4cd8fe54d3a923423f3cd8d136f7

Historical statements such as “current status,” “next step,” and execution
instructions apply to the stage when they were written. Earlier strong
causal interpretations must be read with the final report's limitations.
Passing mechanical tests is not scientific success.

## Environment and execution boundary

Experiments used CPU execution with Python, NumPy, and PyTorch.
Exact versions, seeds, and source hashes are preserved in the run records.
See the [project guide](continual_pilot/README.md) for the environment and
historical command references. Historical commands may overwrite old
results; the archives must remain unchanged. No new scientific run is
authorized by these documentation updates.

## Privacy and license

The [privacy audit](continual_pilot/line2/PRIVACY_AUDIT_2026-09-16.md)
documents the history cleanup and its limits: old commits retained by
GitHub were still accessible by object ID at verification time. Cleaned
branch history must not be confused with complete server-side erasure.

License: [MIT](LICENSE).