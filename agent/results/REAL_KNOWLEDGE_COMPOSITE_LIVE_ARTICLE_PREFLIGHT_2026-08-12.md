# Real Knowledge Composite Live Article V2.2 — Acceptance

**Status:** ACCEPTED — one live response + offline replay  
**Live run date:** 2026-08-12 UTC  
**Final ordinary CI:** 2026-08-12 UTC

## Goal

Validate one reader-facing article built from the already accepted cross-family sum/span contract, using exactly one live provider response and then resolving any deterministic system-gate defects offline rather than paying for repeated regeneration.

## Locked validation identity

- article id: `VAL-RK-COMP-LAST3-SUM-SPAN-V1`
- primary keyword: `分分彩后三和值跨度技巧`
- source refs: `BRBCW-006020`, `BRBCW-002590`
- verified mechanics rule: `SSC-HIST-MECH-3STAR-LAST-V1`
- final candidate-set SHA256: `20e0d1759e51aea0e10d93eb3ccb71af5a2aa5ec659ca72fc8d856cb16a9fa95`

## Frozen machine path

- 后三 ordered candidate space: `1000`
- sum `8–19`: `1000 → 760`, exclude `240`
- span `3–7`: `760 → 534`, exclude `226`
- final space: `534`
- total excluded: `466`

The request is refused before contacting the provider if any locked identity, source/rule ref, count, stage path, exclusion count, candidate hash, or full-list policy changes.

## One live provider run

Only one live provider run was used for this composite article acceptance:

- GitHub Actions run: `31611929191`
- workflow: `real-knowledge-composite-live-v22-temp`
- model: `gpt-5.4-mini`
- requested: `1`
- generated: `1`
- response id: `resp_0387a28a45beb483016a7c8fb4fc088199a786f0aba5f7d202`
- evidence artifact id: `9147577466`
- artifact: `real-knowledge-composite-live-v22-evidence`
- artifact SHA256: `e5cca5ff5f7b4d1cbddcc5bdff5f777845ab9820d3c0435b8826ab6a41e0c549`
- Registry write: `false`
- website write: `false`
- scheduled: `false`
- published: `false`

The model response itself reached:

- Editorial: `100`
- V2.2 Multistage: `100`
- Composite article quality: `90`
- initial repository quality: `65`

The live run was rejected for three reasons:

1. a purely negative safety sentence — `不负责把筛选结果包装成命中率、胜率或推荐号码` — was incorrectly treated as an unsupported positive hard claim;
2. the public-facing `分分彩` label did not match the historical mechanics taxonomy label `时时彩`, even though the immutable verified rule ref correctly identified `SSC-HIST-MECH-3STAR-LAST-V1`;
3. the article clearly stopped after the sum/span two-stage pipeline, but `stop_condition` did not literally contain the characters `第二层` even though `steps` and `next_step_policy` did.

These were system-gate/metadata issues, not reasons to ask the model to rewrite the article.

## Offline fixes — no second provider request

The accepted fix is intentionally narrow:

### 1. Negative safety language

Claim→Evidence now recognizes `不负责把 / 不负责将` as negative safety phrasing. The inverse test remains fail-closed: a sentence such as `不负责把……包装成命中率，但是实际命中率更高` is still treated as a positive performance claim and must not be silently exempted.

### 2. Reader-facing lottery name vs internal mechanics taxonomy

A verified immutable `rule_ref` may prove mechanics even when the reader-facing subject label is `分分彩` and the historical mechanics archive labels the underlying rule family as `时时彩`.

This does **not** rewrite the rule archive or source provenance. It separates two layers:

- internal mechanics/provenance taxonomy: may preserve `时时彩` when technically necessary;
- reader-facing article terminology: prefer `分分彩`.

### 3. Stop-condition metadata

When the model already states that both `和值层` and `跨度层` are completed and stopped, and `steps` / `next_step_policy` explicitly identify the second layer as the terminal layer, the system may canonicalize the `stop_condition` metadata to explicitly say `第二层`.

Article content is not changed.

## New reader-facing terminology policy

For any Draft Packet whose `subject_lottery` is `分分彩`:

- title, SEO title, meta description, primary keyword, summary, tags and normal reader-facing prose should prefer `分分彩`;
- when collected source material contains `时时彩`, the rewritten article should normally express it as `分分彩` rather than mechanically carrying the obsolete reader-facing term forward;
- example/case articles follow the same preference;
- `时时彩` may still appear sparingly when explicitly explaining a historical rule name, internal mechanics category, archive label, or original-source terminology;
- `source_refs`, `rule_refs`, original source archives and historical rule facts must never be rewritten merely to make the display terminology uniform.

The quality gate rejects `时时彩` in core reader-facing SEO/title fields for a `分分彩` subject, and warns on unqualified legacy usage in ordinary body copy.

## Exact-response offline replay

The exact live response is frozen at:

`tests/fixtures/real_knowledge_composite_live_2026_08_12.json`

The replay uses the same response id and the same article content. It does not regenerate or rewrite the content.

Final replay requirements:

- Approval: PASS
- repository quality: `100`
- Editorial: `100`
- V2.2 Multistage: `100`
- Composite article quality: `100`
- article content unchanged: `true`

## Final ordinary CI

Final PR merge-state CI:

- run: `31645333004`
- Python 3.10: SUCCESS
- Python 3.13: SUCCESS
- repository audit: PASS
- Python 3.10 pytest: `337 passed`

This CI includes the exact-response offline replay plus inverse safety tests and the new `分分彩` display-terminology policy tests.

## Paid-path cleanup

After the single live run, the paid path was removed in the required safe order:

1. delete `.github/workflows/real-knowledge-composite-live-v22-temp.yml`;
2. then delete `.github/real-knowledge-composite-live-v22.trigger`.

No automatic retry is configured and no second provider request is required for acceptance.

## Final state boundaries

- live provider responses used for this acceptance: `1`
- automatic retry: `false`
- Registry write: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`

The accepted outcome is therefore not “generate again until it passes.” It is: one real response exposed three deterministic gate defects, those defects were fixed offline, and the exact same response now passes the complete acceptance stack without changing article content.
