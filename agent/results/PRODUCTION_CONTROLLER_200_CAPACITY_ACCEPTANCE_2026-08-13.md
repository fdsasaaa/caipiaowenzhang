# Production Controller 200-Article Capacity Acceptance

**Date:** 2026-08-13  
**Status:** ACCEPTED FOR PRODUCTION GENERATION PRECONDITION

## User target

Generate 200 NEW formal articles that pass the normal article lifecycle and are staged into `articles/approved/`.

The target is a formal Approved inventory target, not a model-call count.

## Initial controller findings

The first production preflight exposed a direct CLI import defect before any provider call. That defect was fixed separately in PR #55 and merged before this acceptance.

After the CLI fix, the original shallow controller probe reported:

- target: 200
- candidate snapshot: 60
- capacity exhaustive: false
- formal inventory before: 0
- provider calls: 0

A maximum read-only probe then proved:

- 19 verified mechanics work units
- probe per work unit: 1000
- ready structurally distinct candidates before global SEO-owner collapse: 287
- exact current SEO owners under the old single-modifier rule: 71
- capacity exhaustive: true

The limiting factor was therefore over-aggressive exact-primary-keyword consolidation, not lack of source/rule-supported article structures.

## SEO ownership correction

V1.4 preserves natural single-method keywords while allowing up to three stable reader-facing method labels for genuinely composite methods.

Examples:

- `分分彩后三直选和值技巧`
- `分分彩后三直选和值跨度技巧`
- `分分彩后三直选和值跨度频率技巧`
- `分分彩后三直选冷热频率奇偶技巧`

`position_filter` remains context only and is not used as a keyword modifier.

The method label order is canonical and independent of source atom order. Quantity never authorizes extra labels, invented techniques, or keyword stuffing.

Offline design comparison across the real ready corpus:

- ready structurally distinct rows: 287
- first 2 labels: 195 unique keyword directions
- first 3 labels: 232 unique keyword directions
- first 4 labels: 233
- all labels: 233

Three labels were selected because they cross the 200 target while avoiding unnecessary long keyword chains.

## Capacity preflight hardening

The controller CLI now performs a cheap first capacity pass. If that pass is both truncated and below target, it automatically reruns a deep zero-provider capacity probe using the policy deep-probe multiplier.

This prevents a shallow snapshot from being mistaken for exhausted content space.

## Authoritative target-200 acceptance

One-shot plan-only workflow run:

- run: `31648271523`
- artifact: `9161589754`
- artifact SHA256: `952808496a853de97764d9700c93e9dc4daf3b63a709f82dbdf935c2f04b84eb`

Repository audit before the plan:

- audit: PASS
- problems: 0
- registry articles: 8
- source records: 2406
- rule gaps: 0
- keyword conflicts: 0

Controller result:

- target: 200
- batch size: 25
- initial shallow candidate snapshot: 90
- initial exhaustive: false
- automatic deep probe executed: yes
- final candidate capacity: **239**
- final capacity exhaustive: **true**
- target feasible: **true**
- attempt budget: 239
- formal Approved inventory before: 0
- provider calls during acceptance: 0
- website sync: false
- scheduling: false
- publication: false

## Production boundary

This acceptance authorizes only proceeding to the separately requested article-generation run.

It does not authorize:

- website cross-repo sync
- website Draft writes
- scheduling
- Publisher invocation
- Publisher cron changes
- publication

Those gates remain separately disabled.
