# Formal Article Production V5 — One-Shot Canary Result

**Date:** 2026-08-13  
**Status:** REJECTED FOR REVISION — system stop-condition matcher gap identified  
**Automatic retry:** false

## Locked canary

- article id: `LCM-IDEA-40be5a222f5cccf7`
- primary keyword: `分分彩五星直选跨度技巧`
- public lottery: `分分彩`
- public play: `五星直选`
- family: `FAM-c93cfcc1527bf6f8`
- source: `BRBCW-002590`
- verified mechanics: `SSC-HIST-MECH-5STAR-DIRECT-V1`
- contract mode: `single_stage`
- method atom: `span_range`
- machine pipeline: `100000 → 43620`
- excluded: `56380`
- provider request cap: `1`

## Paid run evidence

GitHub Actions run:

`31654223608`

Artifact:

- id: `9163742597`
- name: `production-v5-canary`
- ZIP SHA256: `b58bca01cb41f65f568dbecddd76263bfd88eaa8ee169ea3c24d9ce8136c7917`

The formal production controller did not persist provider response IDs in this path, so no response ID is available in the artifact. This is an observability gap, not a reason to invent one.

## Actual controller result

- attempted: `1`
- generated: `1`
- approved: `0`
- formal inventory staged: `0`
- generation failed: `0`
- approval failed: `1`
- multistage failed: `0`
- terminology failed: `0`
- formal inventory errors: `0`
- website sync: `false`
- scheduled: `false`
- published: `false`

The controller stopped after the single locked candidate. There was no automatic retry.

## Quality result

The generated article reached:

- repository Quality: `100`
- Editorial: `90`

Only one Approval error remained:

`stop_condition must explicitly tell the reader when to stop adding filters`

## Exact rejected stop condition

The model wrote:

`如果没有新增且已验证的规则或证据，就必须停在主筛选结果，不继续缩小候选。`

The accompanying next-step policy also said:

`只有新增条件具有已验证规则或证据，并且可以复算时，才允许继续缩小候选；没有这种条件时就停止在主筛选结果。`

This is a clear stop instruction. The rejection came from the V2.1 matcher recognizing only a narrower literal set such as `停止 / 停下 / 不再 / 不得继续 / 不要继续`, while not recognizing the explicit phrases `停在 / 不继续`.

## Previous V3 defects are fixed

The V5 response proves the earlier V3 canary defects are no longer the blocker:

### Machine filter reduction

The article correctly states:

- original space: `100000`
- span rule: `2–6`
- filtered space: `43620`
- removed: `56380`

The primary-filter contract therefore produces a real structured reduction before provider generation.

### Editorial disclaimer metadata

The first claim is now correctly recorded as:

- claim type: `editorial`
- support type: `editorial`
- support refs: `[]`

It is no longer incorrectly treated as an unqualified BRBCW source claim.

## Evidence / terminology state

The rejected Registry lifecycle row preserves:

- source refs: `BRBCW-002590`
- rule refs: `SSC-HIST-MECH-5STAR-DIRECT-V1`
- public subject: `分分彩`
- internal lottery taxonomy: `时时彩`

Post-run repository audit:

- ok: `true`
- registry articles: `9` (includes the rejected lifecycle record)
- sources: `2406`
- rule gaps: `0`
- keyword conflicts: `0`

Reader-terminology audit:

- passed: `true`
- scanned committed reader artifacts: `16`
- FFC artifacts: `16`
- errors: `0`
- warnings: `0`

No formal Approved file was created.

## Paid-path cleanup

After evidence capture, cleanup was performed in safe order:

1. delete `.github/workflows/production-v5-canary-temp.yml`;
2. delete `.github/production-v5-canary.trigger`.

There is currently no V5 paid trigger path.

## System correction path

A separate mainline fix PR is required to recognize narrow explicit stop semantics such as:

- `停在`
- `不继续`
- `无需继续`
- `无需再`
- `到此为止`

The gate must still reject positive continue language and must not degrade to a bare-character `停` match.

The exact V5 stop sentence is used as a regression fixture in that fix.

## Final state

This canary is **not** article 1/200 because it did not pass Approval and was not staged into formal Approved inventory.

No second provider request is justified until the stop-condition semantic gate is fixed, ordinary CI is green, and the exact rejected wording passes offline.
