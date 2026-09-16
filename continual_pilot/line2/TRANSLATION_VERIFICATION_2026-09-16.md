# English publication documentation — verification record

Date: 2026-09-16.

This publication-only update introduces English landing pages and companion
translations. It does not change scientific parameters, rerun experiments,
or reopen the closed research line.

## Preserved originals

The former root and project landing pages were copied byte-for-byte to
[the Turkish root README](../../README.tr.md) and
[the Turkish historical project log](../README.tr.md), respectively.

Their SHA-256 values are:

- Root Turkish README: a6d2a729223c60e84e53817bf16f85f1231c722ab253cd772173209694e97e47
- Turkish project log: cff292a2a35279a19fdfef744a4ab7255ce282cc2c39d80414da1972a189b1f7

The authoritative [Turkish protocol](PREREGISTRATION_DRAFT.md) is unchanged:

0800b0647a0feec22dc13b83ddfaaa7478dc4cd8fe54d3a923423f3cd8d136f7

The Turkish final-results and acceptance-lessons documents are also unchanged.
Preservation was checked against the Git versions preceding this translation update.

## Publication scope

- [English root landing page](../../README.md).
- [English project guide](../README.md): a publication summary, explicitly not
  a full translation of the historical project log.
- [Complete non-normative protocol translation](PREREGISTRATION.en.md):
  the locked Turkish source remains authoritative. References within its
  translated historical text to locking “this file” refer to that source,
  not to a new lock or approval of the English translation.
- [Final results and lessons translation](FINAL_RESULTS_AND_LESSONS.en.md).
- [Historical acceptance-design lesson translation](LESSONS_ACCEPTANCE_2026-09-16.en.md).

The comprehensive protocol's historical plans are not current execution
permission. The original Bitcoin attestation does not timestamp these translations.
Historical commit IDs in translated records were retained rather than silently
replaced following the [privacy rewrite](PRIVACY_AUDIT_2026-09-16.md).

## Checks performed

A read-only document checker compared each full companion translation with
its Turkish source, excluding explicitly separate English publication notes.

- Section counts matched.
- Numeric-token multiplicities matched within every corresponding section,
  after normalizing Turkish decimal commas and thousands separators.
- Confusion-matrix integer lists were handled separately from decimal commas.
- Full SHA-256 values and historical commit IDs matched.
- The authoritative protocol hash and Turkish preservation copies matched.
- All local link destinations in the five English publication documents existed.

There were no numeric-token differences, hash/commit-ID differences, or missing
local destinations in that check. HTML entities used for comparison signs in
two translations are valid Markdown presentation, not numerical discrepancies.

The translation review retained gate failures, strict versus inclusive
boundaries, conditional confidence-interval limitations, diagnostic versus
confirmatory labels, and the explicit unexecuted/future-work boundary.
The English landing pages summarize the source documents; their numeric
statements were reviewed against those sources rather than treated as
line-by-line translations.

## Limits

Matching numeric-token counts is a consistency check, not proof of semantic
equivalence, correct placement of every number, or mathematical correctness.
It is not independent professional translation certification.
Local link existence does not prove that every linked raw artifact is in Git:
large raw records remain release assets, as documented in the landing pages.
Original historical instructions and interpretations remain preserved in
Turkish and must be read in light of the final closure and stated limitations.

No model training, inference, new acceptance search, power calculation, or
scientific test was performed for this publication update.