# Creator-first Batch 300 Acceptance — 2026-08-14

## Scope

- Pull request: #82 — `Add 300 Creator-first approved articles`
- Batch: `CF300-20260813`
- Article paths: `articles/approved/LCM-CREATOR-cf300-20260813-*.json`
- Batch index: `articles/batches/CF300-20260813.json`
- Repository acceptance test: `tests/test_creator_first_batch_300.py`
- Integration branch: `production/creator-first-300-20260814-final`

This acceptance records repository inventory only. It does not schedule, publish, or modify the website.

## Inventory result

Exactly 300 approved article packages are present.

Play distribution:

- 后二直选: 50
- 后三直选: 55
- 五星直选: 55
- 定位胆: 40
- 后二组选: 35
- 后三组选6: 35
- 后三组选3: 30

Style-family count: 20.

## Identity and duplicate gates

Passed:

- 300 unique article IDs
- 300 unique slugs
- 300 unique primary keywords
- 300 unique content hashes
- Local maximum intra-batch lexical similarity: `0.717948717948718`
- Repository lexical duplicate threshold: `0.72`
- Structural intra-batch duplicate gate: passed in PR CI
- Formal Approved validation: passed for all 300 packages in PR CI
- Creator-first Approval validation: passed for all 300 packages in PR CI
- Batch manifest completeness and play distribution: passed in PR CI

No duplicate threshold was lowered to obtain this result.

## Content/provenance prechecks

Passed before repository integration:

- no forbidden/internal reader-facing terms detected
- no content-hash mismatches detected
- no missing claim text detected
- no title missing its primary keyword detected

The integration itself made zero provider/model calls and used no automatic retry.

## CI evidence

PR #82 test workflow Run `31774283444` completed successfully on the rebased head `ebf140597a4e7b60cf33020a7ddb56ee2a551c1d` before this acceptance record was added.

- Python 3.10: `477 passed in 8.88s`
- Python 3.13: `477 passed in 8.89s`
- `python -m engine.cli audit`: `ok: true`
- `rule_gaps`: `0`
- `keyword_conflicts`: `0`

The branch was rebased onto then-current `main` `048bc534f625b0b9a2da5ac547400fd7ff601522`, preserving the concurrent CF50 public-release seed from PR #81.

## Side-effect boundary

- `publication_status` remains inventory-only.
- No website files were modified.
- No publisher cron or schedule was modified.
- No public publication was performed.
- Website ingestion remains a separate downstream responsibility.

## Acceptance

CF300 is accepted as a formal Creator-first article inventory batch, subject to the final PR CI run after this evidence-only record and merge of PR #82.
