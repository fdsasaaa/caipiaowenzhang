# V6 Audited-Angle Remaining-199 Production Readiness

Date: 2026-08-13
Production branch: `production/articles-200-20260813-v6`
Audited-angle architecture merge: `2e9317de05ac8e5a5850c944f6a26beee391715b`
Status: **ZERO-PROVIDER PRODUCTION-CAPACITY GATE PASSED**

## Accepted formal inventory preserved

The existing accepted production canary remains the only formal production article before the remaining-target scan:

- formal production count: `1/200`
- article ID: `LCM-IDEA-40be5a222f5cccf7`
- primary keyword: `分分彩五星直选跨度技巧`
- status: `approved`
- content SHA256: `6a13387d95446d290b2cb604e72494be739910b7ccf0d3a17ff07e40879bf301`

The capacity workflow independently recomputed the content hash from the Approved JSON and required an exact match before planning.

## Main/V6 combined-code acceptance

PR #72 merged the audited article-angle architecture from main into V6 only after the V6 merge-ref passed standard CI in the state containing the accepted canary:

- merge-ref: `0559e959b8fcacb4f87fd9b66b466eb98d47a5dc`
- Python 3.10: SUCCESS
- Python 3.13: SUCCESS
- full suite: `450 passed`
- Registry articles: `9`
- sources: `2406`
- rule_gaps: `0`
- keyword_conflicts: `0`

PR #72 production merge commit:

- `2e9317de05ac8e5a5850c944f6a26beee391715b`

## Remaining-target capacity evidence

Zero-provider run:

- run ID: `31660206433`
- job ID: `94323261175`
- artifact ID: `9165908124`
- artifact SHA256: `1a7c00589d85e5377f3142548be71320e862ee4db57abb5dc88b277f7ee0be6d`
- provider calls: **0**

The run used the formal production planner directly with:

- accepted inventory before planning: `1`
- remaining target: `199`
- lexical duplicate threshold: `0.72`
- structural duplicate threshold: `0.82`
- article angle contract version: `1.0`

Result:

- sustainable candidate capacity: **247**
- target feasible: **true**
- capacity exhaustive: **true**
- attempt budget: `247`
- margin above remaining target: **48**
- post-plan independent pairwise duplicate conflicts: **0**

The planner rejected **1049** near-duplicate angle variants before provider execution:

- lexical duplicate blocks: `967`
- structural duplicate blocks: `82`

Retained machine contract modes:

- single-stage: `80`
- multistage: `167`

Retained audited information-gain distribution:

- `mechanics_case`: `55`
- `space_math`: `72`
- `execution_checklist`: `41`
- `parameter_boundary`: `36`
- `sample_provenance`: `17`
- `multistage_order`: `26`

Every retained candidate was required to have:

- `article_angle_contract_version == "1.0"`
- `angle_contract_verified == true`
- a non-empty deterministic `article_angle_contract`

The candidate pool was then independently checked pairwise again using the same lexical `0.72` and structural `0.82` thresholds. The second check found zero conflicts.

## Safety / operational boundary

This readiness record does **not** claim that the remaining 199 articles have been generated or approved. It proves only that the production branch now has enough machine-contract-backed, mutually non-duplicate candidate capacity to attempt the remaining campaign without lowering thresholds.

During this readiness phase:

- provider calls: `0`
- website sync: disabled
- scheduling: disabled
- publishing: disabled

Temporary capacity workflow and trigger were removed after the evidence artifact was captured.

## Next gate

Any next provider use must be a separately controlled production step. It must not regenerate the accepted `1/200` canary, and should begin with a single new audited-angle article under the current V6 branch before any wider batch is considered.
