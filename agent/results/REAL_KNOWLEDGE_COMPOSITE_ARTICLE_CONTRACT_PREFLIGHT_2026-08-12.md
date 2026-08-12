# Real Knowledge Composite Article Contract — Offline Preflight

**Status:** IMPLEMENTED — ordinary CI pending  
**Date:** 2026-08-12

## Purpose

Turn the accepted two-source sum/span composition into a reader-facing V2.2 article contract without making a provider call.

The article contract must preserve a distinction that the underlying archive actually supports:

- `BRBCW-006020` / `FAM-c7549b61f340ef66` supports the provenance of the `sum_range` atom only;
- `BRBCW-002590` / `FAM-c93cfcc1527bf6f8` supports the provenance of the `span_range` atom only;
- combining the atoms, binding them to `后三直选`, choosing sum-before-span order, and using the numeric ranges `8–19` / `3–7` are system-authored pre-frozen research choices.

No source is allowed to be represented as the author of the combined method.

## Validation-only article identity

- article id: `VAL-RK-COMP-LAST3-SUM-SPAN-V1`
- primary keyword: `分分彩后三和值跨度技巧`
- status: validation-only, unregistered identity
- Registry keyword reservation: false
- site/Registry write: false

This preflight does not claim that the keyword is already reserved for production publication.

## Machine path

The article must explain the exact accepted composition:

- ordered 后三 space: `1000`
- sum `8–19`: `1000 → 760`, exclude `240`
- span `3–7`: `760 → 534`, exclude `226`
- total excluded: `466`
- final count: `534`
- final candidate-set SHA256: `20e0d1759e51aea0e10d93eb3ccb71af5a2aa5ec659ca72fc8d856cb16a9fa95`

## Why the article must not list all 534 candidates

The previous two-digit real-family article had only 26 final values, so listing all values improved auditability without damaging readability.

Here the final set has 534 values. Requiring a full number dump would optimize for a machine artifact rather than a useful article. The contract therefore separates responsibilities:

- **machine evidence** locks the entire 534-set by deterministic enumeration, exact count, and SHA256;
- **reader-facing content** must show the stage arithmetic, formulas, provenance boundaries, stop condition, and a fixed set of deterministic included/excluded spot checks;
- the article must teach a reader how to test any arbitrary three-digit value by computing `sum(digits)` and `max(digits)-min(digits)`.

A large number dump is explicitly treated as a quality failure if it replaces explanation.

## Required source boundary

The article must preserve verbatim:

> 本例有两个独立来源家族：BRBCW-006020只支持和值方法原子的来源归属，BRBCW-002590只支持跨度方法原子的来源归属；把两者组合、先和值后跨度、以及使用和值8–19和跨度3–7，都是系统在看演示样本前预先冻结的研究设计，不是任一来源原文给出的组合方法，也不代表预测优势。

## Required order boundary

The article must preserve verbatim:

> 本实验冻结顺序是先和值、后跨度；即使反过来最终候选集合可能相同，中间路径会从1000→760→534变成1000→690→534，所以不能事后互换顺序再当成同一个实验。

## Reader-facing reproducibility

The prompt and quality gate require:

- exact `1000 / 760 / 534 / 240 / 226 / 466` markers;
- explicit `和值8–19` and `跨度3–7`;
- deterministic included and excluded spot-check values;
- at least two worked examples with actual sum/span calculations;
- formula-level explanation for testing any three-digit number;
- at least six concrete practical steps;
- explicit stop after the second stage;
- synthetic example disclosure (`不是真实开奖记录` semantics);
- no conversion of candidate-space reduction into hit-rate, win-rate, profit, or recommendation claims.

## Negative gates

Tests must fail when:

- the article attributes the combination, order, or thresholds to the sources;
- exact machine path markers are omitted;
- the reader-facing test formula is absent;
- the second-stage stop condition is absent;
- a giant candidate-number dump is used as a substitute for explanation.

## Safety boundaries

- paid model call: `false`
- Registry write: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`

Only ordinary repository CI is justified for this PR. A live model call is a separate later gate, not part of this preflight.