# Real Knowledge Family Matrix — Offline Feasibility Record

**Status:** ACCEPTED DIAGNOSTIC — strict single-family 3–5 matrix is not supported by the current archive; multi-source composition is the evidence-backed next architecture  
**Date:** 2026-08-12

## Goal

After the successful single real-family V2.2 article acceptance, test whether the existing 759-family archive can safely supply 3–5 additional families that each independently contain a complete deterministic 2–3 stage filter pipeline.

No batch AI generation or paid provider call was permitted in this phase.

## Strict eligibility policy

The scan did **not** lower any threshold after observing the result. A family had to satisfy all of the following:

- not the already accepted `FAM-32137acbb90340b9`;
- source support count at least `5`;
- source risk rate at most `0.50`;
- archive lottery mask includes `时时彩` or `分分彩`;
- source example ref exists;
- all family atoms are restricted to `sum_range / span_range / big_small_filter / odd_even_filter`, with optional `position_filter` context only;
- exactly `2` or `3` executable filter atoms;
- archive position mask includes `后二` or `后三`;
- experimental candidate-space binding uses an already verified mechanics rule;
- every frozen stage must shrink candidate space;
- exact final candidate enumeration must equal machine `final_space`.

Cold/hot, frequency, omission, staking, event, follow/kill and other unbound atoms remain fail-closed.

## Verified candidate-space bindings

- archive position `后二` → experimental validation binding `后二直选` → `SSC-HIST-MECH-2STAR-LAST-V1` → ordered `00–99` (`100` outcomes);
- archive position `后三` → experimental validation binding `后三直选` → `SSC-HIST-MECH-3STAR-LAST-V1` → ordered `000–999` (`1000` outcomes).

Every such binding is tagged:

`archive_position_mask_experimental_binding_not_source_play_claim`

The position mask supports a position context only. It does not prove that the archived source prescribed the exact bound play.

## First CI and why it failed

The initial implementation asserted that 3–5 strict candidates must exist. Ordinary CI run `31609112820` correctly failed:

- repository audit: pass;
- existing tests: pass;
- total pytest result: `296 passed, 3 failed`;
- all three new failures had the same root fact: `fewer than three safely executable real families found: 0`.

The system did not respond by relaxing source-support, risk, atom, or play-binding rules. Instead, the selector was converted into an explicit feasibility scan that preserves the original strict policy and reports the filtering funnel.

## Corrected diagnostic CI

Ordinary CI run `31609407867` passed on both Python 3.10 and Python 3.13. The new tests require that an insufficient archive produces a diagnostic / fail-closed result rather than fabricated selections.

## Full-archive offline scan

A one-shot offline workflow scanned the complete compact archive:

- workflow: `real-knowledge-family-feasibility-temp`
- run: `31609489087`
- head SHA: `975183ccb5c491829e5ea25c386321421662899f`
- conclusion: `success`
- paid model/API key: not used
- artifact: `real-knowledge-family-feasibility`
- artifact id: `9146542957`
- artifact SHA256: `b95fca5f2ff06c3d90b564b5807978fc88b5e84c0e0829110cc3238d4c8d18b3`

### Funnel

- total families: `759`
- after excluding already accepted target: `758`
- after source support >= 5: `78`
- after source risk <= 0.50: `35`
- after eligible lottery mask: `35`
- after source example ref: `35`
- excluded because family contains at least one currently unbound atom: `30`
- deterministic-only families remaining: `5`
- deterministic multi-atom families (2–3 executable atoms): `0`
- deterministic single-atom families: `5`
- deterministic single-atom families with a bindable 后二/后三 position: `2`

Therefore the strict single-family matrix result is exactly:

`strict_eligible_count = 0`

This is an archive-content fact under the current policy, not a software failure.

## Evidence-backed composition candidates

The scan found exactly two bindable single-atom families under the same strict source gates and both bind to ordered `后三直选` space:

### 1. Span family

- family: `FAM-c93cfcc1527bf6f8`
- atom family: `position_filter + span_range`
- executable atom: `span_range`
- source: `BRBCW-002590`
- source support: `29`
- source risk: `0.379`
- experimental play: `后三直选`
- rule: `SSC-HIST-MECH-3STAR-LAST-V1`

### 2. Sum family

- family: `FAM-c7549b61f340ef66`
- atom family: `position_filter + sum_range`
- executable atom: `sum_range`
- source: `BRBCW-006020`
- source support: `30`
- source risk: `0.400`
- experimental play: `后三直选`
- rule: `SSC-HIST-MECH-3STAR-LAST-V1`

The scan therefore reports one composition-ready space:

- `ordered_3digit`
- distinct source-backed atoms: `span_range + sum_range`

## Architectural conclusion

The current archive does **not** justify claiming that 3–5 independent real families each already contain their own multi-stage method.

It **does** justify the next research architecture:

> independently source-backed single-atom families → explicit system-authored composition → verified common candidate space → pre-frozen stage parameters → deterministic multistage calculation.

The composition must never be described as a source-authored combined method. Each source family supports only its own atom. Stage ordering, numeric thresholds, and the decision to compose the atoms are system research choices and must be disclosed as such.

The first defensible composite target is therefore:

`BRBCW-006020 / sum_range` + `BRBCW-002590 / span_range` on verified `后三直选` ordered 1000-space.

Using the repository's existing pre-frozen V2.2 research presets, the natural system-authored sequence to validate next is:

`1000 → 和值8–19 → 跨度3–7`

The exact intermediate/final counts must be machine-calculated and frozen before any AI content call; no prediction or profitability claim is implied.

## Cleanup and safety boundaries

The one-shot offline workflow and trigger were removed after evidence capture. No provider workflow or secret was involved.

Throughout this phase:

- paid model call: `false`
- Registry write: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`
- batch generation: `false`
