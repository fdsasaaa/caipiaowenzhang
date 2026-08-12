# Real-Family Group6 Article Offline Preflight

**Date:** 2026-08-13  
**Status:** ACCEPTED  
**Provider calls:** 0

## Purpose

Create the first reader-facing article contract for a real BRBCW family that contains the broad `group3_group6` technique atom, while keeping the exact selected mode and betting-domain compliance provenance-safe.

This phase is offline only. It does not generate an AI article yet.

## Locked validation identity

- article id: `VAL-RK-GROUP6-FAM-F8EFC151-V1`
- primary keyword: `分分彩后三组六技巧`
- real family: `FAM-f8efc151837be787`
- representative source: `BRBCW-004115`
- source support count: `57`
- source risk rate: `0.439`
- verified mechanics rule: `SSC-HIST-MECH-3STAR-GROUP6-V1`
- internal rule taxonomy: `时时彩`
- reader-facing lottery label: `分分彩`

## Provenance boundary

The source archive currently proves only that the family contains the broad group-method atom. It does not preserve an exact matched source phrase that would prove the source selected 组六.

The article must therefore preserve exactly:

> BRBCW-004115只支持该家族包含组选类方法原子的来源归属；本例选择组六是系统在查看演示样本前预先冻结的验证选择，不是来源原文指定或推荐的组六模式，也不代表预测优势。

The mode owner is `system_research`, not `source`.

## Group6 domain mechanics

The system-research group6 binding locks:

- candidate unit domain: unordered group bet units;
- complete group6 unit count: `120`;
- each group6 unit contains three distinct digits;
- one unit covers `6` ordered permutations;
- complete ordered group6 structure size: `720`;
- complete ordered three-digit universe: `1000`.

Example unit `{1,2,3}` covers:

`123 / 132 / 213 / 231 / 312 / 321`.

Counterexamples:

- `112` → group3 structure, not group6;
- `777` → triple-same, neither group3 nor group6.

## Critical coverage-denominator boundary

The article must preserve exactly:

> 组六的120个无序投注单位组成整个组六目标域；每个单位覆盖6个有序排列，因此对应720个组六结构的有序开奖结果。720/1000=72%只表示组六结构占全部三位有序结果的比例，不是本项目的可执行投注覆盖率；若把120个单位全部使用，对组六目标域覆盖率是100%，超过90%上限，因此本文不得把“全120单位”写成可执行投注方案。

This distinction is mandatory:

- `720 / 1000 = 72%` → descriptive global three-digit structure share;
- `120 / 120 = 100%` → target-play coverage if every group6 unit is used;
- project executable coverage ceiling → `<= 90%` of the selected play's target domain;
- therefore full-domain group6 execution → blocked.

## Article quality strategy

The article may explain the full 120-unit group6 **domain**, but must not dump all 120 units as a betting list.

Reader-facing content should instead explain:

1. source provenance vs system-selected group6 mode;
2. three-distinct-digit group6 mechanics;
3. unordered bet unit vs six ordered outcomes;
4. why 120 units map to 720 ordered group6 outcomes;
5. how `112` and `777` differ structurally;
6. why 72% is not the executable coverage denominator;
7. why full 120-unit usage would be 100% target-play coverage and is blocked.

## Negative gates

The custom article quality gate rejects:

- `BRBCW-004115推荐组六`;
- `来源推荐组六` / `来源指定组六`;
- `72%低于90%所以可以全投`;
- `120个全部投注` / `全120单位投注`;
- any `normalized_bets` field in this validation article;
- a giant 120-unit-style number dump used instead of explanation;
- legacy `时时彩` in reader-facing title/SEO/meta/primary-keyword fields.

## Practical stop condition

This article is a mechanics/domain explanation only.

After explaining the group6 domain and deterministic examples, the article must stop. Any actual betting subset requires a separate future contract that:

- selects `<=90%` of the group6 target domain;
- has a defensible pre-frozen selection rule;
- separately passes the amount/prize/economics gate;
- does not inherit permission merely from this domain article.

## CI evidence

Ordinary PR CI:

- run: `31648242644`
- merge-ref commit: `963b7478386f62a54db91628b2b8059cef21a2b6`
- merge-ref combines preflight head `a2a4381169f506264636ce8d96d2e5a35f335572` with main `78b28bf51d3f404da1b1f7ef806eff2ac1485bde`
- Python 3.10: SUCCESS
- Python 3.13: SUCCESS
- repository audit: PASS
- pytest: `375 passed`
- registry articles: `8`
- source records: `2406`
- rule gaps: `0`
- keyword conflicts: `0`

The test suite includes positive article-contract acceptance and inverse gates for source misattribution, wrong 72% executable inference, normalized_bets, large unit dumps, and legacy reader-facing `时时彩` terminology.

## Global execution state

`group3_group6` remains absent from the global executable atom whitelist.

A successful article preflight does not make arbitrary group families executable.

## Safety boundaries

- provider call: `false`
- Registry write: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`
- normalized bets: `false`
- full-domain group6 portfolio: `blocked`

## Next gate

The offline contract is now strong enough to justify at most one validation-only live model call. Any such run must remain one-shot, non-publishing, and must pass both the standard Approval stack and this custom group6 article gate. No live workflow is part of this preflight PR.
