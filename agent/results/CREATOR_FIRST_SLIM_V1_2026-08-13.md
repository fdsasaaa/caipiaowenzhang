# Creator-first Slim V1 Acceptance

**Date:** 2026-08-13  
**Status:** ACCEPTED — offline architecture validation  
**Provider calls:** 0

## Why this change exists

The previous production architecture accumulated increasing amounts of Planner, finite candidate-capacity, Article Angle, parameter-binding and batch orchestration logic. Those systems were useful for proving correctness and discovering failure modes, but they had begun to decide what the model was allowed to create.

The new design reverses that relationship:

> **The model creates. The repository validates, calculates and remembers.**

The objective is not to fill a finite pre-enumerated pool. It is to repeatedly create genuinely different, coherent and useful lottery articles across plays, techniques, data-research ideas, bankroll design, staking/progression design and hybrid ideas, while preserving strict rule/evidence/compliance boundaries.

## New default creator path

Creator-first V1 creates one article at a time:

1. load verified gameplay mechanics;
2. load a bounded memory of existing articles for anti-duplication context;
3. let the model freely choose one verified play and invent the article technique/design;
4. return a thin creator manifest plus the article in one structured response;
5. build a minimal Draft Packet after the creative choice has been made;
6. run the existing hard validators;
7. stage only a fully approved result;
8. remember it in GitHub for the next creation.

The default Creator-first path does **not** require:

- Planner candidate enumeration;
- Article Angle assignment;
- candidate-capacity preflight;
- a predeclared finite topic pool;
- automatic model retries.

## New files

- `policies/CREATOR_FIRST.json`
- `engine/creator_first.py`
- `engine/creator_style.py`
- `scripts/create_article.py`
- `docs/CREATOR_FIRST_ARCHITECTURE.md`
- `tests/test_creator_first.py`

## What remains strict

The slimming is not removal of validation. Creator-first continues to reuse the existing repository gates for:

- verified gameplay mechanics;
- Claim → Evidence;
- bet compliance;
- lexical and structural duplicate detection;
- SEO primary-keyword ownership;
- reader-facing terminology;
- Approved Package / Registry integrity.

It adds only a very small human-style gate that blocks internal engineering vocabulary and obvious repeated batch-template prose. It does not prescribe a fixed outline or fixed number of sections.

## Creativity ownership

The model may decide:

- which verified play to use;
- the technique idea;
- one or multiple conceptual methods;
- the case/explanation style;
- whether the article is technique, data-research, bankroll, staking/progression or hybrid;
- the SEO wording;
- when a simple method is better than a complicated one.

Existing source articles and previous Approved articles are memory/inspiration, not mandatory templates.

## Bankroll and staking/progression

Creator-first explicitly supports bankroll and staking/progression research.

When platform/provider economics are not verified, the creator must prefer:

- relative stake units;
- bankroll exposure;
- drawdown/risk path;
- stop conditions;
- sequence behaviour.

It must not invent platform payout, rebate or guaranteed-profit facts. Verified provider economics can be added later without changing the creator-first architecture.

## Draw-data boundary

Creator-first V1 sets `draw_data_available=false` deliberately.

The repository's existing generic evidence vocabulary currently distinguishes verified rules, sources and synthetic cases, but does not yet provide a clean first-class evidence channel for verified historical draw datasets. Therefore V1 does not allow the model to claim it used historical draw data when none was explicitly supplied.

The next draw-data extension should be small:

`verified draw-data file → creator context/evidence → same creator → same validators`

No return to a complex Planner is required.

## Human reader style

Reader-facing copy must be concise, clear and human. The small Creator-style gate blocks internal engineering vocabulary such as:

- Draft Packet
- Blueprint
- angle_delivery
- claim_evidence
- provider_response_id
- candidate_capacity
- article_angle_contract
- system_research
- 机器合同 / 工程合同

It also flags excessive generic batch-template phrasing, while leaving the actual structure and voice to the model.

## Compatibility strategy

The first slimming phase is intentionally non-destructive.

The following existing components remain in the repository for rollback, research and optional legacy batch workflows:

- Planner;
- Article Angle Contract;
- candidate-capacity preplanning;
- V2.2 multi-stage filter contracts.

They are no longer the conceptual default for Creator-first article generation.

## CI history

### Initial run

Run `31661997201` exposed one narrow compatibility issue in the new tests:

- a legitimate original article used `source_refs=[]` because it did not claim a source article;
- a purely explanatory article used `claim_evidence=[]` because it made no hard claim;
- legacy `review_draft()` treats empty list values in `required_fields` as missing.

The global review gate was **not** weakened.

Creator-first was instead changed locally so:

- Structured Output still requires both fields to exist;
- Creator-first explicitly validates both are lists;
- original Creator-first articles require `source_refs == []`;
- Claim→Evidence still validates the evidence list;
- those two fields are not put through the legacy non-empty-value check.

### Final accepted CI

Run: `31662099057`

- Python 3.10: SUCCESS
- Python 3.13: SUCCESS
- repository audit: PASS
- pytest: `458 passed`
- Registry articles: `8`
- source records: `2406`
- rule gaps: `0`
- keyword conflicts: `0`

Final tested merge-ref:

`ff3b68cf43b196dcab91a0853c61f6369b2f2be7`

which combines Creator-first head `4bb0a0797ab1d4792bb7db4a9c865177281f42d1` with main `8130c6d4db0b751e398140c3ab783116e0e4d5ab`.

The fake-transport test proves the Creator-first path makes exactly one model request when executed, uses `store=false`, captures `response_id`, and does not require Planner, Article Angle or capacity metadata.

## Safety / side-effect state

- real provider calls during this PR: `0`
- automatic retry: `false`
- website sync: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`

## Next gate

After merge, the correct next validation is **one real Creator-first canary**:

- exactly one provider request;
- no automatic retry;
- model freely selects a verified play/technique;
- manual review of whether the prose is genuinely simple and human;
- normal Approval/dedup/compliance checks;
- no batch expansion until that single article demonstrates the desired creative quality.

The first slimming milestone is complete when this architecture lands on `main`; batch production should not be resumed before the real Creator-first canary is reviewed.
