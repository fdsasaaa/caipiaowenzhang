# Daily partial-batch retention

## Decision

The daily production target remains 20 website-ready public-r1 articles and the operational minimum remains 10. The formal inventory commit floor is now 1.

This is a batch-retention change only. It does not lower any article-level gate.

- 20+ website-ready public-r1: `PASS_TARGET`
- 1-19 website-ready public-r1: `PASS_PARTIAL_QUALITY_FIRST`
- 0 website-ready public-r1: fail closed (`BLOCKED_BELOW_MINIMUM`)

The workflow continues to refill toward 20 until candidate/cost/refill capacity is exhausted. It does not stop early merely because one article passed.

## Why

A website-ready public-r1 article has already passed generation, Approval, dedupe, keyword ownership, public safety, terminology, editorial and repository gates. Discarding an entire day because only 8 rather than 10 such articles survived does not improve the quality of those 8 articles; it only destroys qualified inventory.

`operational_minimum=10` remains a production-health signal. A day producing fewer than 10 should be visible in diagnostics and may trigger investigation, but it does not invalidate otherwise qualified articles.

## Invariants

This change does not:

- lower Approval thresholds;
- lower public-r1 safety gates;
- relax dedupe;
- relax primary-keyword ownership;
- revive frozen CF50 items;
- change website/CMS/Publisher/schedule/cron responsibilities;
- make an empty day successful.

Historic failed-run diagnostics remain audit evidence. Content bytes that were never committed cannot be reconstructed from hashes alone and must not be fabricated.
