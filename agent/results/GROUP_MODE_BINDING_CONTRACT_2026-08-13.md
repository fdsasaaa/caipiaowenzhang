# Group Mode Binding Contract

**Date:** 2026-08-13  
**Status:** ACCEPTED  
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

System-research group6 binding produces:

- group mode: `group6`;
- candidate unit domain: unordered group bet units;
- candidate unit count: `120`;
- ordered outcome coverage: `720 / 1000`;
- coverage rate: `72%`;
- mechanics rule: `SSC-HIST-MECH-3STAR-GROUP6-V1`;
- source_did_not_choose_mode: true.

System-research group3 binding produces:

- candidate unit count: `90`;
- ordered outcome coverage: `270 / 1000`;
- coverage rate: `27%`;
- mechanics rule: `SSC-HIST-MECH-3STAR-GROUP3-V1`.

These are deterministic mechanics calculations, not performance claims.

## Freeze rule

`group_mode` must be fixed before any evaluation sample is inspected.

If `frozen_before_observation=false`, binding fails.

The generic archive label `group3_group6` is not accepted as a mode and cannot silently default to either group3 or group6.

## Global execution state remains unchanged

This PR does **not** add `group3_group6` to `EXECUTABLE_ATOM_ORDER`.

A successful parameter binding is local validation metadata, not permission to execute arbitrary group families globally.

## Reader terminology

Public article copy should use `分分彩` where practical. Historical mechanics metadata retains the internal `时时彩` taxonomy label.

## CI evidence

Final pull-request merge-ref CI:

- run: `31647624918`
- merge ref: `8e2a23bc01eb00d7da626eed6c19b89200b723f3`
- merge ref combines head `287aaf0a144461130c13e7a3d66b6719ed7ef4e8` with main `3be80aa27d59fd986aef12aff9f33a054873c071`
- Python 3.10: SUCCESS
- Python 3.13: SUCCESS
- repository audit: PASS
- pytest: `366 passed`
- registry articles: `8`
- source records: `2406`
- rule gaps: `0`
- keyword conflicts: `0`

The main-side change included by this merge ref is PR #55, which fixes the production-controller CLI module path and does not overlap this group-mode binding implementation.

## Safety boundaries

- provider calls: `0`
- Registry write: `false`
- website write: `false`
- scheduled: `false`
- published: `false`
- production eligible: `false`

## Next gate

Use the accepted system-research binding to build **one offline article preflight** for `FAM-f8efc151837be787`, using group6 as the pre-frozen validation mode. The article contract must state clearly that BRBCW-004115 supports only the broad group-method provenance; `group6` is the system's pre-frozen validation choice, not the source's recommendation.
