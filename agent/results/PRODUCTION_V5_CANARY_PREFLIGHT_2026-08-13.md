# Formal Article Production V5 — Canary Preflight

**Date:** 2026-08-13  
**Status:** READY BUT NOT TRIGGERED  
**Provider calls from V5:** 0

## Campaign baseline

V5 starts from strict production main commit:

`0f57a9eb7b073f2c65bc5999eabb2bef43baf32c`

Formal Approved inventory at branch start:

`0`

The strict exhaustive campaign preflight remains:

- target: `200`
- candidate capacity: `216`
- single-stage candidates: `86`
- multistage candidates: `130`
- capacity exhaustive: `true`
- target feasible: `true`
- provider calls during capacity/preflight: `0`
- website sync: `false`
- scheduling: `false`
- publishing: `false`

## Offline V5 preflight evidence

GitHub Actions run:

`31653644186`

Artifact:

- id: `9163512266`
- name: `production-v5-preflight`
- SHA256: `52c10acbab4f965a3c994dec117572dc25d786b675aafc6abc6978648c089f81`

The preflight re-enumerated the complete campaign and locked the first canary without a provider request.

## Hard-locked canary

The future paid canary is not allowed to substitute another candidate.

Expected identity:

- article id: `LCM-IDEA-40be5a222f5cccf7`
- primary keyword: `分分彩五星直选跨度技巧`
- public lottery: `分分彩`
- public play: `五星直选`
- real technique family: `FAM-c93cfcc1527bf6f8`
- source ref: `BRBCW-002590`
- verified mechanics rule: `SSC-HIST-MECH-5STAR-DIRECT-V1`
- contract mode: `single_stage`
- method atom: `span_range`
- method atoms covered: `span_range`

Machine pipeline:

- candidate domain: ordered five-digit direct results
- starting space: `100000`
- system research span preset: `2–6`
- final space: `43620`
- excluded: `56380`
- stage count: `1`
- source recommendation claimed: `false`
- predictive advantage claimed: `false`

The paid workflow now checks these exact values before provider transport. Any identity, capacity, family, keyword, rule, source, method or count drift stops the job before the model call.

## Provider request cap

The V5 paid canary workflow exists but has **no trigger**.

When eventually triggered, it will:

1. re-check strict campaign capacity;
2. build the target-1 controller plan;
3. hard-lock the exact candidate above;
4. truncate `candidates` to exactly one;
5. set `attempt_budget=1`;
6. allow at most one generation attempt;
7. use no automatic retry;
8. persist only if generated=1, approved=1, staged=1 and all audit/terminology/hash checks pass.

A failed canary is evidence, not permission to retry automatically.

## Persistence boundary

A passing canary is committed only to:

- `articles/approved/*.json`
- `registry/articles.jsonl`

It then counts as article `1/200`.

The canary workflow does not sync the website, schedule a draft, or publish an article.

## Stale V4 isolation

A parallel/stale V4 campaign had already started a 25-article paid run before strict all-method production PR #66 was merged:

- V4 run: `31651767807`
- stale workflow: `production-batch25-01-temp`
- old run was still executing its provider/controller step when V5 was prepared.

The old V4 workflow and trigger were removed from the V4 branch after the stale run had begun. The V4 branch was advanced by those cleanup commits, so the stale checkout cannot fast-forward its old formal outputs into the current V4 branch through its original push step.

Because the available GitHub connector exposes no cancel-run action, the already-running provider step cannot be truthfully described as cancelled. It remains historical exposure until GitHub completes the job.

No V5 paid request will be triggered while that stale V4 provider step is still running.

Any V4 outputs are historical evidence only and do not count toward the final 200-article V5 campaign.

## Terminology boundary

The formal reader-facing policy remains unchanged:

- generated article title/SEO/normal prose should prefer `分分彩`;
- `时时彩` is not allowed in FFC core reader-facing fields;
- raw source evidence and internal historical mechanics may preserve `时时彩` when that is the actual provenance taxonomy.

## Next gate

Before creating `.github/production-v5-canary.trigger`:

1. confirm stale V4 run `31651767807` is no longer executing;
2. inspect its final evidence and verify its stale push did not alter the current V4 branch;
3. only then trigger exactly one V5 canary request.
