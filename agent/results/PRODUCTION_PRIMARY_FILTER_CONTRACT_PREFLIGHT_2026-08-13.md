# Production Primary Filter Contract Preflight

**Date:** 2026-08-13  
**Status:** OFFLINE PREFLIGHT ACCEPTED

## Why this change exists

The first strictly single-call production acceptance generated a structurally valid article with Hard Quality 100 but failed Editorial/Approval because the model had not been given a machine-frozen primary filter interval and exact candidate-space reduction. The model was being asked to invent a value that must instead be computed before generation.

## New production rule

Every candidate admitted by the Article Production Controller must now receive a machine-built `primary_filter_spec` before any provider request.

The contract records:

- executable technique atom
- play and selector
- candidate-space type
- frozen parameters
- parameter basis
- starting candidate count
- after-filter candidate count
- excluded count
- stop-after-primary-filter instruction
- explicit non-predictive research scope

A contract is invalid unless `0 < after_filter_space < starting_space`.

## Supported candidate domains

- ordered one-digit: 10
- ordered two-digit: 100
- ordered three-digit: 1,000
- ordered four-digit: 10,000
- ordered five-digit: 100,000
- two-digit group unordered: 45
- three-digit group3: 90
- three-digit group6: 120

`后二大小单双` remains fail-closed because its categorical betting semantics are not represented by the numeric candidate-space contract.

## Supported primary methods

Static exhaustive filters:

- sum_range
- span_range
- odd_even_filter
- big_small_filter
- repeat_number
- neighbor_number (difference=1; 0/9 are not circular neighbors)

Synthetic-case parameterized filters:

- cold_hot_split
- frequency_window
  - fixed lookback=12
  - fixed top_n=3
  - digit pool calculated from deterministic synthetic demonstration data
- omission_threshold
  - fixed threshold=2
  - fixed lookback=12
  - only at one fixed position

The parameter is frozen by Python/system policy before prose generation. A smaller candidate set is never described as evidence of higher hit rate, future predictive advantage, or profitability.

## Exact regression examples

- 五星直选跨度 2–6: `100000 -> 43620`, excludes `56380`
- 后二直选和值 6–12: `100 -> 58`, excludes `42`
- 后二组选邻号: `45 -> 9`
- 后三直选 fixed top-3 frequency digit pool: `1000 -> 27`

## Capacity evidence

Zero-provider run before machine-contract binding:
- run `31650665835`
- total eligible candidate snapshot: 230
- static deterministic primary coverage: 195
- non-static-only candidates: 35
- provider calls: 0
- artifact `9162438139`
- SHA256 `e4eb7a4237ab02657350e6636c22aa323587ac4260ef84eef9dfd3d5f750bec2`

After machine contracts were required by `discover_candidate_portfolio`:
- run `31650989765`
- **machine-contract candidate capacity: 227**
- capacity exhaustive: true
- target 200 remains feasible
- play families retained: 17
- `后二大小单双` intentionally removed from production capacity
- provider calls: 0
- artifact `9162553677`
- SHA256 `b2588b13bfcf9ece009d6aaabb5b8bb8662507273393af1f9a18a90a01431604`

## Claim-evidence hardening

The production controller also applies a narrow metadata-only normalization:

- pure editorial scope/disclaimer text incorrectly labeled `source_unverified` may be normalized to `editorial`;
- source attribution, numeric claims, calculations, performance/economics claims and prose are never rewritten by this rule.

The Draft Packet now explicitly tells the model that literal forbidden guarantee terms remain forbidden even when used negatively and that editorial scope disclaimers use editorial evidence metadata.

## Safety boundary

This preflight used no provider calls and performed no Registry/Approved inventory write. Website sync, website Draft creation, scheduling and publication remain disabled.
