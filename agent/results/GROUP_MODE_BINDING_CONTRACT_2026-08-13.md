# Group Mode Binding Contract

**Date:** 2026-08-13  
**Status:** ACCEPTED — coverage denominator corrected  
**Production eligibility:** false

## Purpose

The group-domain contract proved the mechanics of 组三 and 组六, but the compact BRBCW family archive collapses both terms into the same `group3_group6` atom.

This contract prevents the execution/article layer from pretending that a source selected a mode when the archived evidence does not preserve that exact source phrase.

## Two binding bases

### 1. `source_exact_phrase`

This is the strongest provenance path.

Requirements:

- family must contain `group3_group6`;
- requested source_ref must match the family's representative provenance ref;
- a materialized source article must exist under `knowledge/source_articles/<BRBCW-ID>.json`;
- that source text must explicitly contain a term corresponding to the selected mode:
  - group3: `组三 / 组选3 / 组选三`;
  - group6: `组六 / 组选6 / 组选六`.

The current `knowledge/source_articles/` directory is empty, so current real families **cannot** pass this path yet. Compact family metadata alone is intentionally insufficient.

### 2. `system_research_prefrozen`

This path exists for validation/research articles.

The system may choose `group3` or `group6` before any evaluation sample is inspected, but the binding explicitly records:

- mode owner = `system_research`;
- the BRBCW family/source supports only the broad `group3_group6` provenance atom;
- the selected mode is **not** a source recommendation;
- validation_only = true;
- production_eligible = false.

## First machine-bound validation example

Family:

- `FAM-f8efc151837be787`
- representative source: `BRBCW-004115`
- archive atoms: `group3_group6 + position_filter`

System-research group6 binding describes the full group6 **domain**:

- group mode: `group6`;
- candidate unit domain: unordered group bet units;
- domain unit count: `120`;
- ordered group6 structure size inside the complete `000–999` universe: `720`;
- global three-digit structure share: `720 / 1000 = 72%`;
- mechanics rule: `SSC-HIST-MECH-3STAR-GROUP6-V1`;
- source_did_not_choose_mode: true.

System-research group3 binding describes the full group3 domain:

- domain unit count: `90`;
- ordered group3 structure size inside `000–999`: `270`;
- global three-digit structure share: `270 / 1000 = 27%`;
- mechanics rule: `SSC-HIST-MECH-3STAR-GROUP3-V1`.

These are deterministic mechanics/domain calculations, not performance claims.

## Important coverage-denominator correction

`72%` and `27%` above are **not executable betting coverage rates**. They only describe how much of the complete ordered three-digit universe has the corresponding multiplicity structure.

The project's executable coverage ceiling must use the **selected play's own target domain** as denominator.

Therefore:

- using all `120` group6 units would cover `100%` of the group6 target play domain;
- using all `90` group3 units would cover `100%` of the group3 target play domain;
- the project ceiling is `<= 90%`;
- therefore an all-domain group3/group6 portfolio is **not allowed as an executable betting example**.

The binding contract now exposes separate fields:

- `global_three_digit_structure_share` — descriptive only;
- `target_play_domain_coverage_if_all_units_used` — `1.0` for the full domain;
- `target_coverage_ceiling_for_executable_portfolio` — `0.90`;
- `all_domain_units_executable_portfolio_allowed` — `false`.

The ambiguous old field `coverage_rate` is removed so it cannot be reused with the wrong denominator.

This correction does not invalidate the mechanics or source-provenance binding. It tightens the execution/compliance interpretation before any article or portfolio is generated.

## Freeze rule

`group_mode` must be fixed before any evaluation sample is inspected.

If `frozen_before_observation=false`, binding fails.

The generic archive label `group3_group6` is not accepted as a mode and cannot silently default to either group3 or group6.

## Global execution state remains unchanged

This contract does **not** add `group3_group6` to `EXECUTABLE_ATOM_ORDER`.

A successful parameter binding is local validation metadata, not permission to execute arbitrary group families globally.

## Reader terminology

Public article copy should use `分分彩` where practical. Historical mechanics metadata retains the internal `时时彩` taxonomy label.

## Original binding CI evidence

The provenance-safe binding first passed:

- run: `31647624918`
- Python 3.10: SUCCESS
- Python 3.13: SUCCESS
- repository audit: PASS
- pytest: `366 passed`

A separate correction PR adds explicit denominator regression tests before the next group6 article preflight.

## Safety boundaries

- provider calls: `0`
- Registry write: `false`
- website write: `false`
- scheduled: `false`
- published: `false`
- production eligible: `false`
- all-domain executable group portfolio: `false`

## Next gate

After the denominator-correction CI is green, build one offline group6 article preflight for `FAM-f8efc151837be787`. The article may explain the full 120-unit group6 **domain**, but it must not present “all 120 units” as a compliant executable betting portfolio. Any later executable example must select `<=90%` of the target group6 domain and independently pass the amount/economics gate.
