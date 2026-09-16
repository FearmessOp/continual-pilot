# Publication privacy audit — 2026-09-16

## Status and scope

The advertised Git history has been cleaned. **Complete removal from GitHub has not been achieved:** an old commit remained publicly accessible by its object ID and retained the old email metadata at the remote check on 2026-09-16T17:48:31.158980+00:00.

The owner authorized hiding the personal email while retaining the real author name. Future repository-local commits use the GitHub noreply address. This maintenance did not run any scientific experiment, change a scientific decision, or reopen the closed research line.

## Inspection coverage

| Scope | Before cleanup | After cleanup |
|---|---:|---:|
| Worktree files inspected | 4291 | 4291 |
| Distinct reachable historical file blobs inspected | 438 | 434 |
| Files inside downloaded release archives | 3861 | 3861 |
| NPY arrays inspected across scopes | 18612 | 18612 |
| Pickle streams disassembled across scopes | 232 | 232 |
| Pickle GLOBAL references encountered | 876 | 876 |
| Unresolved inspections | 0 | 0 |

Counts across scopes overlap; they are not counts of unique scientific observations. History inspection included patch output from all advertised local refs, starting at the first commit. Author and committer email fields were also checked separately.

Text, filenames, archive member names, serialization metadata, NPY headers and string fields were inspected. Pickle opcodes were disassembled without executing them. Numeric tensor storage was not interpreted as text. One final D checkpoint was additionally loaded on CPU with restricted weights-only loading; its model, optimizer, utility, routing, memory and counter structure was inspected without training or inference.

The release scan used previously downloaded external copies and rechecked archive SHA-256 values against their indices. Earlier full member-by-member download verification is recorded in [the v0.4 backup evidence](BACKUP_V04_VERIFICATION_2026-09-16.json) and [the v0.5 backup evidence](BACKUP_V05_VERIFICATION_2026-09-16.json).

## Findings and corrections

Four historical reports contained an absolute personal output directory in the nested configuration output field:

- [Diagnostic summary](../results_diagnose/summary.json).
- [v0.2 generator summary](../results_generator_v02/summary.json).
- [v0.3 generator summary](../results_generator_v03/summary.json).
- [Combined learner summary](../results_v02/summary.json).

There were 4 occurrences in historical blobs and 8 occurrences in patch output, totaling 12 Windows-home matches. The corresponding 12 username-token matches describe the same paths, not additional disclosures. The current versions already used repository-relative output directories; the first historical versions were brought into agreement.

The original 10 commits contained 20 personal email fields: one author and one committer field per commit. Patch output separately exposed 10 author-header occurrences. All 20 fields were replaced with the approved GitHub noreply identity. Names, timestamps and commit messages were retained; parent IDs necessarily changed.

For each affected report, parsed JSON content was verified equal after excluding only the configuration output field. All other scientific content was unchanged. The old and rewritten final Git tree object IDs were identical. A private rollback bundle and detailed old/new commit mapping were retained locally, outside publication.

## Post-cleanup scan

The expanded final scan reported:

| Pattern | Occurrences |
|---|---:|
| Windows or Unix home paths | 0 |
| Known personal email | 0 |
| Local username token | 0 |
| Absolute Windows paths | 0 |
| UNC paths | 0 |
| Unix installation paths | 0 |
| Cache paths | 0 |
| Local machine name | 0 |
| General email candidates | 10 |
| IPv4-like candidates | 3 |

All 10 email candidates were the approved noreply address. All 3 IPv4-like candidates were repetitions of a dotted byte total in [the v0.4 report](REPORT_CONTROL_V04_01.md:90), its historical blob and patch output, not network addresses. An intermediate broad path expression produced 46 URL-derived false positives; adding a left boundary removed these, without modifying any inspected content.

No actionable personal paths or emails were found in the release archives. No checkpoint, numerical array, manifest or release archive was rewritten or repackaged. This is a contextual, pattern-based audit, not proof that every conceivable personal-information encoding is absent. Receipt/image formats were not OCR-scanned, and numeric storage was outside text inspection.

## Remote verification and preservation

The public branch and both release tags were rewritten with explicit force-with-lease protection in an atomic push. Both release target metadata fields were subsequently updated and verified through the public API:

| Reference | Cleaned commit |
|---|---|
| Audited master tip | 37df990c9241e073d35d515262ba405d6e64b272 |
| archive-v04-control-01 | ebbceee7be3b7746aedb3d24a39f445c6be08f2d |
| archive-v05-final-01 | dea58df3698a1c4c501e9a03c9abd22090e3d060 |

The public API confirmed all 20 email fields across the 10 cleaned commits used noreply. Release asset IDs, sizes and reported digests remained unchanged. Existing scientific records that cite old commit IDs remain historical records; those IDs are not the current branch/tag identities.

The authoritative [Turkish protocol](PREREGISTRATION_DRAFT.md) was preserved byte-for-byte throughout the rewrite. Its SHA-256 remains:

0800b0647a0feec22dc13b83ddfaaa7478dc4cd8fe54d3a923423f3cd8d136f7

## Remaining privacy limitation

Rewriting branches and tags does not erase server-retained objects, cached views, forks or earlier clones. Direct public access to an old commit was tested and still exposed the old email metadata. No GitHub Support removal request has been submitted by this maintenance process.

The repository owner can request GitHub Support review of retained sensitive commit data and cached views. Removal eligibility and completion must be confirmed by GitHub; neither is guaranteed here. Private local rollback material and reflogs also retain original metadata and must not be published. The clean reachable-history scan must not be represented as complete erasure from the hosting service or third-party copies.