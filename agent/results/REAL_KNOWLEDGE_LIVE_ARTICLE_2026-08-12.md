# Real Knowledge Live Article V2.2 — Acceptance Record

**Status:** IN PROGRESS — first provider attempt stopped at transport before generation  
**Date:** 2026-08-12

## Locked target

- article: `LCM-IDEA-bf5a9864b004ae17`
- family: `FAM-32137acbb90340b9`
- source: `BRBCW-003787`
- selected-source support count: `6`
- verified mechanics: `SSC-HIST-MECH-LAST2-BSOE-V1`
- atoms: `big_small_filter + odd_even_filter`
- model: `gpt-5.4-mini`

## Frozen content contract

The machine path remains:

- ordered 后二 candidate space: `100`
- stage 1 / 一大一小: `100 → 50`, exclude `50`
- stage 2 / 一单一双: `50 → 26`, exclude `24`
- full pipeline: `100 → 26`, total exclude `74`

The article must print all final values:

`05 07 09 16 18 25 27 29 36 38 45 47 49 50 52 54 61 63 70 72 74 81 83 90 92 94`

It must also preserve the exact source/parameter boundary: the archived source family supports the size/parity technique atoms, while the specific one-big-one-small and one-odd-one-even counts are pre-frozen system research parameters, not source-stated parameters or evidence of predictive advantage.

## Ordinary preflight CI

Before any provider call:

- run `31606607325`: success
- audit: pass
- Python 3.10 pytest: `293 passed`
- Python 3.13 job: success

After installing the temporary one-shot workflow, ordinary run `31606903531` also passed before the trigger was written.

## Provider attempt 1 — transport failure

- workflow: `real-knowledge-live-v22-temp`
- run: `31606955898`
- head SHA: `f81b400f641a78dae01d3425229aeae07c611f2e`
- requested: `1`
- generated: `0`
- approved: `0`
- workflow conclusion: `failure`
- failure layer: provider transport, before model generation / article evaluation
- endpoint: `https://api.synapai.top/v1/responses`
- provider response: HTTP `502`, Cloudflare `origin_bad_gateway`
- provider metadata: `retryable=true`, `retry_after=60`
- artifact: `real-knowledge-live-v22-evidence`
- artifact id: `9145510769`
- artifact SHA256: `9d3c44feb3c52ae8d02f1ae52f29b41e7cc1e2ce4f9da0cec68bbba3f7eb38b0`

This attempt is **not** classified as an article-quality failure because no structured model output was generated and none of Approval, multistage quality, or real-knowledge quality could run.

## Retry policy

Because the provider explicitly classified the 502 as retryable and no content/system gate was reached, exactly one targeted transport retry is permitted after the provider's backoff interval. It must reuse the identical target and frozen contract. No code/prompt/threshold change is allowed between attempt 1 and the retry.

If the targeted retry also fails at provider transport, this acceptance cycle stops as provider-unavailable; no third paid request is allowed in this cycle.

## State boundaries

Throughout both preflight and provider attempts:

- Registry write: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`
- no batch generation
- no automatic retry loop
