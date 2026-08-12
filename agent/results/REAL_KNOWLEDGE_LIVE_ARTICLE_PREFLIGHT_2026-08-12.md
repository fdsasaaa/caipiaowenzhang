# Real Knowledge Live Article V2.2 — Preflight

**Status:** IMPLEMENTED — ordinary CI pending  
**Date:** 2026-08-12

## Goal

Validate one existing source-backed article through the V2.2 AI + Approval path with substantially stronger reader-facing requirements than the earlier batch2 article.

This is not a new benchmark and not a publication run. The target is locked to the existing identity:

- article: `LCM-IDEA-bf5a9864b004ae17`
- family: `FAM-32137acbb90340b9`
- source: `BRBCW-003787`
- selected-source support count: `6`
- verified mechanics: `SSC-HIST-MECH-LAST2-BSOE-V1`
- atoms: `big_small_filter + odd_even_filter`

## Why this revision-quality validation exists

The earlier approved batch2 article explains how to classify 后二 digits by size/parity, but it does not prove that the production AI can explain a real source-backed family as a strict, sequential candidate-space workflow with concrete final candidate values.

This acceptance therefore requires more than generic Approval PASS.

## Frozen machine contract

The existing source family determines the two technique atoms only. System research parameters are frozen before viewing the synthetic example:

1. ordered 后二 space `00–99`: `100`
2. exactly one big digit + one small digit: `100 → 50`, exclude `50`
3. exactly one odd digit + one even digit: `50 → 26`, exclude `24`
4. full pipeline: `100 → 26`, total exclude `74`
5. stop after stage two

The exact final 26 values are:

`05 07 09 16 18 25 27 29 36 38 45 47 49 50 52 54 61 63 70 72 74 81 83 90 92 94`

## Mandatory source / parameter boundary

The generated article must include verbatim:

> 本例的“大小”和“单双”来自系统已登记的来源家族；“一大一小”和“一单一双”是系统在看演示样本前预先固定的研究参数，不是来源原文参数，也不代表预测优势。

The source therefore supports method-family provenance, not the numerical research preset, hit rate, profitability, or predictive value.

## Mandatory concrete-candidate requirement

The generated article must not stop at counts. It must print the complete final candidate line with all 26 two-digit values, including leading zeroes. The dedicated real-knowledge quality gate fails if the model gives only `100 → 50 → 26` without the actual values.

## Code path

- `engine/filter_pipeline.py`: exposes deterministic final candidate enumeration after the same validated pipeline predicates.
- `engine/real_knowledge_live_validation.py`: reconstructs a validation-only V2.2 blueprint from the existing registry identity + static family archive; freezes provenance, pipeline, final candidates, and write/publish boundaries.
- `engine/real_knowledge_ai_generation.py`: adds a specialized prompt contract while retaining the existing V2.2 structured-output, normalization, and immutable-identity checks.
- `scripts/real_knowledge_live_article_v22.py`: single-article fail-closed preflight/live runner.
- `tests/test_real_knowledge_live_validation.py`: validates exact provenance, machine contraction, candidate list, prompt requirements, evidence normalization, and failure when concrete candidates or provenance boundaries are omitted.

## Safety and state boundaries

- paid model call during preflight: `false`
- Registry write: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`
- no batch generation
- no automatic retry

The live runner uses `evaluate_for_approval`, V2.2 `evaluate_multistage`, and a separate `evaluate_real_knowledge_article` gate. A live result is accepted only if all three pass.

## Execution rule

1. ordinary repository CI must pass first;
2. only then may a one-shot temporary paid workflow be introduced;
3. exactly one article / one provider request is allowed for the first attempt;
4. if it fails, preserve the evidence and diagnose the system-level cause; do not blind-rerun;
5. remove the paid workflow before removing its trigger;
6. keep Registry / website / schedule / publication frozen throughout.
