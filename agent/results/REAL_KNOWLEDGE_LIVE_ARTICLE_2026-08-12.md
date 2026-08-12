# Real Knowledge Live Article V2.2 — Acceptance Record

**Status:** ACCEPTED — one real model response passes the final code path by deterministic offline replay; no third provider request was used  
**Date:** 2026-08-12

## Locked target

- article: `LCM-IDEA-bf5a9864b004ae17`
- family: `FAM-32137acbb90340b9`
- source: `BRBCW-003787`
- selected-source support count: `6`
- verified mechanics: `SSC-HIST-MECH-LAST2-BSOE-V1`
- atoms: `big_small_filter + odd_even_filter`
- model: `gpt-5.4-mini`

This cycle validates one existing source-backed article identity. It does not create a competing SEO article and it does not publish or write a draft to the website.

## Frozen content contract

The machine path is:

- ordered 后二 candidate space: `100`
- stage 1 / 一大一小: `100 → 50`, exclude `50`
- stage 2 / 一单一双: `50 → 26`, exclude `24`
- full pipeline: `100 → 26`, total exclude `74`

The article must print all final values:

`05 07 09 16 18 25 27 29 36 38 45 47 49 50 52 54 61 63 70 72 74 81 83 90 92 94`

It must preserve the exact reader-facing source/parameter boundary:

> 本例的“大小”和“单双”来自系统已登记的来源家族；“一大一小”和“一单一双”是系统在看演示样本前预先固定的研究参数，不是来源原文参数，也不代表预测优势。

The source family therefore supports method-atom provenance. It does not prove the research preset, future hit rate, profitability, or predictive advantage.

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

This attempt is not classified as an article-quality failure because no structured model output was generated and none of Approval, multistage quality, or real-knowledge quality could run.

## Provider attempt 2 — targeted transport retry

Because attempt 1 was explicitly provider-retryable and never reached model generation, exactly one targeted transport retry was allowed after the provider backoff interval. The article target, prompt contract, model, thresholds, and frozen candidate pipeline were unchanged.

- workflow: `real-knowledge-live-v22-temp`
- run: `31607187832`
- head SHA: `42f5b7e34255cf4ad997de294687b91f4922b1e7`
- requested: `1`
- generated: `1`
- workflow conclusion: `failure` under the pre-fix Approval metadata path
- response id: `resp_036fce91418f96a3016a7c83a3bd888193ba8e4ea8c48ed625`
- title: `分分彩后二大小单双技巧：100组后二号码按大小、单双两层筛到26组怎么复算`
- primary keyword: `分分彩后二大小单双技巧`
- quality score: `100`
- editorial score: `100`
- multistage score: `100`
- real-knowledge score: `100`
- artifact: `real-knowledge-live-v22-evidence`
- artifact id: `9145623249`
- artifact SHA256: `6505ab12b3557b1b4bc4ef42f350c5ae560370c5988d61aa19886fa1a6e5b38f`

The generated content itself satisfied every dedicated content requirement:

- exact source/parameter boundary present;
- exact `100 → 50 → 26` sequence present;
- stage exclusions `50` and `24` present;
- total exclusion `74` present;
- all 26 final two-digit values printed with leading zeroes preserved;
- practical steps and stop condition present;
- synthetic-data disclosure present;
- no predictive-advantage claim introduced.

The pre-fix Approval result had exactly two Claim → Evidence metadata errors:

1. `claim_evidence[0] unverified source claim must be explicitly qualified`
2. `claim_evidence[5] synthetic_case must reference only case_bundle`

## Root cause

Neither error was a factual/content failure.

### Evidence row 0

The body already stated that the research parameters are **not source-original parameters** and **do not represent predictive advantage**. The evidence row used `source_unverified + BRBCW-003787`, but the generic source qualifier gate only recognized phrases such as “未独立验证”; it did not recognize this source/parameter-boundary wording as an explicit qualification.

### Evidence row 5

The claim `整体共排除74个。` is not a synthetic sample result. It is the deterministic aggregate `100 - 26 = 74` from the frozen machine filter pipeline. The model tagged it `synthetic_case` with a source ref, while the system can prove it from the verified gameplay rule + frozen pipeline.

## Deterministic evidence normalization

No provider retry was used after diagnosing these two rows. Instead, the final code adds a narrow real-knowledge evidence normalizer that is allowed to change metadata only when the fact is machine-deterministic:

- the exact source/parameter boundary evidence is explicitly marked `来源内容未独立验证；...` while the **article body remains byte-for-byte unchanged**;
- the exact aggregate exclusion claim `整体共排除74个。` is converted from `synthetic_case` to `verified_rule` with `SSC-HIST-MECH-LAST2-BSOE-V1`;
- nearby non-exact claims such as `整体共排除74个，因此更容易中奖。` are deliberately **not** upgraded.

The full captured response is preserved at:

- `agent/results/REAL_KNOWLEDGE_LIVE_RESPONSE_2026-08-12.json`

This makes the acceptance reproducible without another paid call.

## Offline replay acceptance

Ordinary CI run `31608020248` replays the exact captured provider response against the final normalization path.

Required regression behavior is enforced in tests:

1. before normalization, the captured response must reproduce exactly the two historical Approval errors;
2. normalization must leave `article.content` unchanged;
3. only Claim → Evidence rows `0` and `5` may change;
4. after normalization, Approval must pass with Quality `100` and Editorial `100`;
5. Multistage must pass at `100`;
6. Real-Knowledge must pass at `100`;
7. the unsafe near-match negative test must remain unmodified / fail closed.

CI evidence:

- run: `31608020248`
- Python 3.10: success
- Python 3.13: success
- repository audit: pass
- Python 3.10 pytest: `296 passed`

The accepted statement is therefore precise: **the one real generated response from attempt 2 passes the final V2.2 real-knowledge code path when replayed through deterministic evidence normalization, without changing its article content and without making a third provider request.** The historical workflow result remains failure and is not rewritten as a successful live run.

## Paid-path cleanup

After attempt 2, no additional provider call was justified. The paid path was removed in safe order:

1. delete `.github/workflows/real-knowledge-live-v22-temp.yml`;
2. only after the workflow was gone, delete `.github/real-knowledge-live-v22.trigger`.

No third provider request is permitted for this acceptance cycle.

## State boundaries

Throughout the entire cycle:

- Registry write: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`
- no batch generation
- no automatic retry loop

This acceptance validates article-generation and approval quality only. It does not establish predictive advantage, profitability, or provider economics.
