# Real-Family Group6 Live Path — Offline Preflight

**Date:** 2026-08-13  
**Status:** IMPLEMENTED — ordinary CI pending

## Goal

Prepare exactly one validation-only live model request for the accepted real-family group6 article contract, while proving the entire request/acceptance path offline first.

No provider workflow is included in this PR.

## Locked request target

- article: `VAL-RK-GROUP6-FAM-F8EFC151-V1`
- keyword: `分分彩后三组六技巧`
- family: `FAM-f8efc151837be787`
- source: `BRBCW-004115`
- group mode: `group6`
- mode owner: `system_research`
- verified mechanics rule: `SSC-HIST-MECH-3STAR-GROUP6-V1`
- compliance policy: `USER-BET-COMPLIANCE-90-V1`
- unordered group6 unit domain: `120`
- ordered group6 structure size: `720`
- global structure share: `72%`
- full target-play domain coverage if all units used: `100%`
- executable coverage ceiling: `90%`
- full-domain execution: `false`
- normalized bets: `false`

Any drift in these fields stops before provider transport.

## Evidence separation

The live path uses three distinct evidence types:

1. `source_unverified` + `BRBCW-004115`
   - supports only broad group-method provenance;
   - does not say the source selected 组六.
2. `verified_rule` + `SSC-HIST-MECH-3STAR-GROUP6-V1`
   - supports group6 mechanics and deterministic unit/outcome-domain facts.
3. `policy_contract` + `USER-BET-COMPLIANCE-90-V1`
   - supports the internal 90% executable-coverage ceiling;
   - is explicitly an internal guardrail, not a platform rule;
   - cannot prove performance or prediction claims.

The standard generic article schema is not globally broadened. `policy_contract` is added only to the structured-output schema used by this group6 validation generator.

## Offline fake-transport acceptance

Tests exercise the exact live generator without any network call:

- strict structured JSON schema;
- exact prompt boundaries;
- source/rule/policy evidence normalization;
- article content remains byte-for-byte unchanged by evidence normalization;
- standard Approval stack;
- group6 custom quality gate.

Expected offline result:

- Approval PASS;
- repository quality 100;
- Editorial 100;
- group6 custom quality 100.

## Fail-closed tests

The generator refuses before transport if:

- group mode changes;
- source/system mode ownership changes;
- unit count changes;
- target-play full-domain coverage stops being `1.0`;
- full-domain execution becomes allowed;
- normalized bets become allowed.

The Claim→Evidence layer also rejects:

- unknown policy refs;
- use of `policy_contract` without a Draft Packet policy;
- attempts to use policy evidence to prove performance/prediction claims.

## Runtime behavior after CI

Only if ordinary CI passes may a temporary one-shot workflow be added.

That workflow must:

- make at most one provider request;
- use `gpt-5.4-mini` through the existing provider relay;
- never retry automatically;
- save the full result/summary as an artifact;
- keep Registry/site/schedule/publish writes false;
- be removed before final merge.

A failed first model output is evidence, not permission to loop until success.
