# Real Knowledge Composite Live Article V2.2 — Preflight

**Status:** IMPLEMENTED — ordinary CI pending  
**Date:** 2026-08-12

## Goal

Run exactly one real model-generation acceptance for the already accepted cross-family sum/span article contract, but only after ordinary CI proves the live runner and evidence normalization are fail-closed.

## Locked validation identity

- article id: `VAL-RK-COMP-LAST3-SUM-SPAN-V1`
- primary keyword: `分分彩后三和值跨度技巧`
- source refs: `BRBCW-006020`, `BRBCW-002590`
- verified mechanics: `SSC-HIST-MECH-3STAR-LAST-V1`
- final candidate-set SHA256: `20e0d1759e51aea0e10d93eb3ccb71af5a2aa5ec659ca72fc8d856cb16a9fa95`

## Frozen machine path

- 后三 ordered candidate space: `1000`
- sum `8–19`: `1000 → 760`, exclude `240`
- span `3–7`: `760 → 534`, exclude `226`
- final space: `534`
- total excluded: `466`

The request is refused before contacting the provider if any locked identity, source/rule ref, count, stage path, exclusion count, candidate hash, or full-list policy changes.

## Content acceptance

A generated article must pass all three gates:

1. repository `Approval` (hard quality + editorial + Claim → Evidence);
2. V2.2 multistage gate;
3. composite article quality gate.

The composite quality gate requires source separation, system-authored composition disclosure, exact `1000 → 760 → 534`, deterministic spot checks, formulas for testing any arbitrary three-digit number, and a stage-two stop condition. Dumping a large candidate list is a failure rather than a quality improvement.

## Evidence normalization boundary

The normalizer is intentionally narrow and may alter **Claim → Evidence metadata only**, never article content.

It canonicalizes exactly three locked statements:

- the two-source provenance boundary → explicit `source_unverified` qualifier with both source refs;
- the frozen-order comparison → deterministic calculation evidence under the verified rule;
- the 534-count / candidate-hash integrity statement → deterministic calculation evidence under the verified rule.

Near-match claims that add unsupported conclusions such as “更容易中奖” are not normalized.

## Execution rule

1. ordinary CI must pass first;
2. only then create a temporary one-shot live workflow;
3. exactly one provider request is allowed for the first attempt;
4. no automatic retry;
5. preserve evidence whether pass or fail;
6. remove workflow before trigger after the run;
7. Registry / website / schedule / publication remain frozen.

## State boundaries

- current paid model call: `false`
- Registry write: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`
