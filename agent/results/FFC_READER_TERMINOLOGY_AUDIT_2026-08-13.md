# FFC Reader Terminology Audit

**Date:** 2026-08-13  
**Status:** ACCEPTED

## Purpose

Enforce the reader-facing terminology policy without corrupting internal historical mechanics or source provenance.

For articles whose public subject is `分分彩`, reader-facing fields should normally use `分分彩`, not `时时彩`.

## Reader-facing fields audited

- title
- seo_title
- meta_description
- primary_keyword
- secondary_keywords
- search_intent
- summary
- category
- tags
- content

## Explicitly not treated as reader-facing leakage

Internal fields such as:

- `lottery`
- `play`
- `rule_refs`
- `source_refs`
- historical mechanics rule records
- source archive provenance

may preserve `时时彩` when that is the technically correct historical/internal taxonomy.

## Repository artifact scope

The audit scans committed JSON article artifacts under:

- `articles/approved/*.json`
- `articles/drafts/*.json`
- `articles/published/*.json`
- `smoke/batch*/articles/*.json`
- `smoke/batch*/approved/*.json`

The canonical `articles/*` inventories are currently empty except for `.gitkeep`; current reader-facing samples therefore come from smoke batch 1 and batch 2.

## Accepted current result

Current committed audit population:

- smoke batch 1 article JSON: `3`
- smoke batch 1 approved JSON: `3`
- smoke batch 2 article JSON: `5`
- smoke batch 2 approved JSON: `5`
- total scanned reader article artifacts: `16`
- FFC reader article artifacts: `16`
- reader-facing legacy `时时彩` findings: `0`

No existing committed reader article needs terminology rewriting at this point.

## Policy

For an FFC reader article:

- `时时彩` in core reader-facing metadata is an error;
- unqualified `时时彩` in ordinary body copy is an error;
- a body sentence may retain `时时彩` only when it explicitly identifies a historical rule, internal rule-library/mechanics taxonomy, archive term, or original-source terminology.

This is not blind text replacement. The audit must never rewrite source archives or internal rule taxonomy.

## Inverse gates

Tests prove that:

- internal `lottery=时时彩` does not trigger a reader-facing error;
- `title=时时彩后三技巧` for an FFC article is rejected;
- ordinary body copy using `时时彩` without historical/source qualification is rejected;
- an explicit historical/internal taxonomy explanation may retain the term.

## CI evidence

Ordinary PR CI:

- run: `31645834183`
- Python 3.10: SUCCESS
- Python 3.13: SUCCESS
- repository audit: PASS
- pytest: `341 passed`
- registry articles: `8`
- source records: `2406`
- rule gaps: `0`
- keyword conflicts: `0`

## Safety boundaries

- provider calls: `0`
- Registry write: `false`
- website write: `false`
- scheduled: `false`
- published: `false`

The audit now becomes a permanent repository-level regression gate, so future staged/draft/approved FFC article artifacts cannot silently reintroduce obsolete reader-facing `时时彩` terminology.
