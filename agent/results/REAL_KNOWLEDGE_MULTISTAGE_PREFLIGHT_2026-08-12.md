# Real Knowledge Multistage Preflight

**Status:** IMPLEMENTED — ordinary CI pending  
**Date:** 2026-08-12

## Purpose

Move V2.2 from synthetic benchmark-only multistage validation into a source-backed technique-family validation path.

The first acceptance target is the already approved real-family article `LCM-IDEA-bf5a9864b004ae17`, backed by family `FAM-32137acbb90340b9` and source `BRBCW-003787`. The family contains `big_small_filter + odd_even_filter` and has six supporting selected sources in the compact archive.

## Scope

This preflight is deliberately offline and non-publishing:

- paid model call: false
- Registry write: false
- website draft write: false
- scheduled: false
- published: false

It validates source provenance, deterministic candidate-space enumeration, frozen stage parameters, and fail-closed conversion rules only.

## Source / Parameter Boundary

The source family supports **which technique atoms belong together**. It does not prove that any specific threshold, count, hit rate, or profit statement is true.

Therefore numeric filter parameters are explicit system research presets frozen before any synthetic draw is produced or inspected. They are tagged `system_research_preset_not_source_claim` and must not be presented as source-stated values or predictive evidence.

Sample-dependent atoms such as `cold_hot_split`, `frequency_window`, or `omission_threshold` are not silently converted. A family containing an unbound atom is rejected rather than partially represented as an executable method.

## New Candidate Space

`engine/filter_pipeline.py` gains `ordered_2digit`, enumerating all ordered pairs `00` through `99` (100 candidates). This is required for real 后二大小单双 / 二星直选-style position-sensitive filters; the previous `unordered_2digit` 45-pair space cannot represent ten-position + unit-position order.

## First Real-Family Contract

For `FAM-32137acbb90340b9` / 后二大小单双:

1. start from ordered two-digit space: `100`
2. pre-frozen size structure: exactly one big digit and one small digit → expected `50`
3. pre-frozen parity structure: exactly one odd digit and one even digit → expected `26`
4. stop after the source-backed second stage

Expected contraction: `100 → 50 → 26`.

These stage settings are research-case parameters, not claims that this structure has future predictive advantage.

## Tests Added

The branch tests require:

- the real family to exist in the compact 759-family archive with `BRBCW-003787` provenance and support count 6;
- the existing approved article to bind the historical verified rule `SSC-HIST-MECH-LAST2-BSOE-V1`;
- exact machine counts `100 → 50 → 26`;
- all Registry / website / scheduling / publication flags to remain false;
- a real `cold_hot_split` article to fail closed instead of receiving invented parameters;
- a three-stage deterministic research case to contract `1000 → 760 → 534 → 210`;
- partial conversion of a family with an unbound atom to be rejected.

## Acceptance Gate

Do not perform a paid model call in this PR. Merge only after ordinary repository CI is green. A later real AI article-quality call, if justified, must be a separate explicit acceptance step with the paid path temporary and publishing still frozen.
