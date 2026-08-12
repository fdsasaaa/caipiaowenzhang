# Real Knowledge Family Matrix — Offline Selection Preflight

**Status:** IMPLEMENTED — ordinary CI and one-shot offline selection evidence pending  
**Date:** 2026-08-12

## Goal

Expand from the single accepted real family into a small, structurally diverse real-family matrix **without** starting batch AI generation.

The matrix selector reads the complete compact BRBCW family archive (759 families derived from 2406 selected sources) and only considers source-backed families that can be converted into a deterministic 2–3 stage candidate-space experiment without inspecting a sample first.

## Eligibility policy

A family is eligible only when all of the following hold:

- family is not the already accepted `FAM-32137acbb90340b9`;
- source support count is at least `5`;
- source risk rate is at most `0.50`;
- archive lottery mask includes `时时彩` or `分分彩`;
- all family atoms are limited to the deterministic set `sum_range / span_range / big_small_filter / odd_even_filter`, plus optional `position_filter` context;
- there are exactly `2` or `3` executable filter atoms;
- a source example ref exists;
- archive position mask includes `后二` or `后三` so the experiment can be bound to a verified ordered candidate space;
- every frozen filter stage actually shrinks the candidate space;
- final candidate enumeration exactly matches the final machine count.

Families containing cold/hot, frequency-window, omission, staking, follow/kill, event-dependent or other unbound atoms are rejected rather than partially converted.

## Verified candidate-space bindings

The matrix uses only verified mechanics already present in the repository:

- archive position `后二` → experimental validation binding `后二直选` → `SSC-HIST-MECH-2STAR-LAST-V1` → ordered space `00–99` (`100` outcomes);
- archive position `后三` → experimental validation binding `后三直选` → `SSC-HIST-MECH-3STAR-LAST-V1` → ordered space `000–999` (`1000` outcomes).

This binding is explicitly tagged:

`archive_position_mask_experimental_binding_not_source_play_claim`

The archive position mask supports *where the family has appeared*. It does **not** prove that the source article prescribed the exact bound play. The binding is a system research choice for reproducible validation only.

## Selection policy

Candidates are ranked by:

1. more filter stages first;
2. lower source-risk rate;
3. higher source-support count;
4. stable family id.

The selector first seeks both ordered two-digit and ordered three-digit spaces where eligible families exist, then fills the remaining slots with structurally distinct atom signatures. The requested matrix size is 3–5 families; default is 5.

## Safety boundaries

- paid model call: `false`
- Registry write: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`
- no batch article generation
- no provider workflow

The immediate next gate is ordinary CI. Only after CI passes will a one-shot **offline** workflow run the selector and preserve the exact chosen families as evidence.