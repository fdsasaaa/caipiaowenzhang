# Real Knowledge Atom Gap Ranking

**Date:** 2026-08-13  
**Status:** IMPLEMENTED — ordinary CI pending

## Why this phase exists

The accepted 759-family feasibility scan proved that 35 real families pass the source support/risk/lottery/example gates, but 30 are excluded because at least one technique atom is not currently machine-executable.

The current executable whitelist remains unchanged:

- `sum_range`
- `span_range`
- `big_small_filter`
- `odd_even_filter`

`position_filter` remains context only.

This phase does **not** enable any additional atom. It ranks the gaps before implementation.

## Ranking questions

For every currently unbound atom appearing in those otherwise-qualified families, the offline report calculates:

- number of blocked families containing the atom;
- number of those families with a bindable 后二/后三 position;
- number that already contain an existing executable atom;
- total source-support count and average source-risk rate;
- how many bindable families would become structurally complete if **only that one atom** were added;
- how many would structurally become a strict 2–3 stage family if **only that one atom** were added.

The last two are structural estimates only. They do not mean a filter operator already exists.

## Conservative automation classes

### Deterministic semantics ready, operator still missing

- `repeat_number`
- `neighbor_number`

Both already have explicit semantics that can be evaluated from a candidate number/window without first inspecting a historical sample. They are candidates for future engineering, not automatically enabled features.

### Sample-parameter contract required

- `cold_hot_split`
- `frequency_window`
- `omission_threshold`

These depend on a historical sample window and/or threshold. They remain fail-closed until the system can prove where the window/threshold came from and that it was frozen before looking at the evaluation sample.

### Missing or insufficient domain contract

Atoms such as event-follow/kill, staking, stop-loss/win, carry mapping and other archive labels without a complete semantics/operator contract remain blocked regardless of frequency.

## Safety principle

Popularity in the archive is not enough to justify automation. Priority should favor an atom only when:

1. its semantics are explicit;
2. its parameters can be frozen without post-hoc sample fitting;
3. adding it materially unlocks bindable real families;
4. its candidate-space operation can be independently enumerated and tested.

## Boundaries

- paid model call: `false`
- Registry write: `false`
- website write: `false`
- scheduled: `false`
- published: `false`
- no new atom enabled in this PR

The immediate gate is ordinary repository CI. After CI passes, a one-shot **offline** Actions run may be used only to capture the exact full-archive ranking as an artifact; it requires no provider secret.
