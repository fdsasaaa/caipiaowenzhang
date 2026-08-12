# Real Knowledge Atom Gap Ranking

**Date:** 2026-08-13  
**Status:** ACCEPTED — corrected offline full-archive ranking

## Why this phase exists

The accepted 759-family feasibility scan proved that 35 real families pass the source support/risk/lottery/example gates, but 30 are excluded because at least one technique atom is not currently machine-executable.

The current executable whitelist remains unchanged:

- `sum_range`
- `span_range`
- `big_small_filter`
- `odd_even_filter`

`position_filter` remains context only.

This phase does **not** enable any additional atom. It ranks the gaps before implementation.

## Frozen funnel

- total real families: `759`
- pass source support/risk/lottery/example gate: `35`
- blocked by at least one unbound atom: `30`
- strict policy changed: `false`

## Authoritative corrected scan

- GitHub Actions run: `31646551503`
- workflow run number: `3`
- execution: offline only
- artifact id: `9160932239`
- artifact: `real-knowledge-atom-gap-ranking`
- artifact SHA256: `0ae1c2c62a212c420585676d2f1cec961cd25de58bbbeb913efbca288fc93658`

The structural-unlock counters only credit a family when the family actually contains the proposed new atom and all its other atoms are already executable/context-only. This prevents unrelated already-executable families from inflating a candidate atom's value.

## Corrected ranking

| atom | class | blocked | bindable | unlock if only this atom added | strict 2–3 stage unlock | source support sum | avg risk |
|---|---|---:|---:|---:|---:|---:|---:|
| `neighbor_number` | deterministic semantics ready | 1 | 1 | 1 | 0 | 7 | 0.1430 |
| `omission_threshold` | sample parameter required | 3 | 1 | 1 | 1 | 22 | 0.3000 |
| `cold_hot_split` | sample parameter required | 5 | 1 | 0 | 0 | 33 | 0.3004 |
| `frequency_window` | sample parameter required | 4 | 0 | 0 | 0 | 21 | 0.2750 |
| `group3_group6` | missing semantics/domain contract | 6 | 5 | 2 | 1 | 149 | 0.3375 |
| `dan_candidate` | missing semantics/domain contract | 7 | 4 | 2 | 1 | 136 | 0.2637 |
| `kill_candidate` | missing semantics/domain contract | 4 | 2 | 2 | 1 | 77 | 0.2970 |
| `compound_selection` | missing semantics/domain contract | 10 | 4 | 1 | 0 | 98 | 0.2433 |
| `consecutive_number` | missing semantics/domain contract | 1 | 1 | 1 | 0 | 5 | 0.4000 |
| `progressive_staking` | missing semantics/domain contract | 6 | 2 | 0 | 0 | 37 | 0.2827 |
| `follow_after_event` | missing semantics/domain contract | 1 | 0 | 0 | 0 | 5 | 0.0000 |

## What the ranking means

### `neighbor_number`

This is the only currently encountered blocked atom that already has explicit sample-independent semantics and can be evaluated from the candidate itself. It appears in one otherwise-qualified family:

- family: `FAM-50e50ea52316b78e`
- source: `BRBCW-000431`
- support: `7`
- risk: `0.143`
- archive positions include `后三`

Adding a correct neighbor-number operator could unlock that one family, but it would not by itself create a new strict 2–3-stage family. Therefore it is low-risk engineering, but low leverage.

`repeat_number` is **not** present in the 30 currently blocked otherwise-qualified families. Its semantics may exist, but this archive scan provides no reason to prioritize it now.

### `omission_threshold`

This is the highest-leverage atom among the semantics-defined sample-dependent group:

- blocked families: `3`
- bindable: `1`
- one-atom structural unlock: `1`
- strict multistage unlock: `1`

The important family is `FAM-2f9db30394e685e1` (`odd_even_filter + omission_threshold + position_filter`, source `BRBCW-006580`). It could become a genuine two-stage real-family article, but only after the system has a non-post-hoc contract for omission lookback/window/threshold provenance. It must remain fail-closed until then.

### `group3_group6`

This is strategically much larger than `neighbor_number`:

- blocked families: `6`
- bindable by current position heuristic: `5`
- one-atom structural unlock: `2`
- strict multistage unlock: `1`
- source support sum: `149`

However it currently has **no formal semantics/domain contract**. This is important because 组三/组六 is a play/result-structure domain, not automatically just another filter over an ordered 后三直选 space. The current position heuristic is insufficient evidence to enable it.

### `dan_candidate`

Also high leverage:

- blocked families: `7`
- bindable by current position heuristic: `4`
- one-atom structural unlock: `2`
- strict multistage unlock: `1`
- source support sum: `136`

But `胆码` is ambiguous until the contract states whether a candidate digit must occur at least once, at a fixed position, within a 组选 set, or under some other source-specific rule. It must not be generalized from the label alone.

### Other high-frequency atoms

`compound_selection`, `kill_candidate`, `progressive_staking`, and event-follow concepts remain blocked. Their archive frequency is not evidence that a safe deterministic candidate-space operator exists.

## Scan-history integrity

Three temporary offline workflow runs occurred; none used a provider secret:

1. run `31646298563` — failed before ranking because direct script execution lacked `PYTHONPATH`; no ranking produced.
2. run `31646353287` — produced a report but exposed an accounting bug: structural unlocks credited families that did not contain the candidate atom. That report is **not authoritative**.
3. run `31646551503` — after adding the membership guard and regression test, produced the authoritative corrected ranking above.

The accounting bug is permanently covered by a test requiring:

`bindable_blocked_family_count >= structural_bindable_unlock >= structural_strict_multistage_unlock`.

## Engineering priority conclusion

Do not implement atoms merely in the order of implementation ease or archive frequency.

Recommended next investigation order:

1. define exact **domain/semantics contracts** for `group3_group6` and `dan_candidate`, because they have substantially higher real-archive leverage;
2. independently define the **sample pre-freeze contract** needed by `omission_threshold` before considering it executable;
3. keep `neighbor_number` as a low-risk fallback implementation candidate if the higher-leverage domain contracts cannot be made precise;
4. do not prioritize `repeat_number` yet because the current qualified blocked-family set contains no demand for it.

No atom becomes executable merely because it is ranked.

## CI evidence

Corrected ranking code and regression guard first passed ordinary CI at run `31646502012` on Python 3.10 and 3.13.

While this PR was open, `main` advanced through PR #53 (`article-production-controller`) to `d5cb557aa71199fcb95bfa0bdca25cd5a70144f6`. PR #53 changed only production-controller files and did not overlap the ranking implementation.

A final synchronization commit forced the pull-request merge ref to be retested against that newer `main`:

- final integration CI run: `31646855596`
- merge-ref commit: `e2ec2d783f644e58c4161e7f36363e9c883e6849`
- merge-ref message: `Merge dd0e12f8579c757298fc3d8c5824dc026ddfc66d into d5cb557aa71199fcb95bfa0bdca25cd5a70144f6`
- Python 3.10: SUCCESS
- Python 3.13: SUCCESS
- repository audit: PASS
- pytest: `352 passed`
- registry articles: `8`
- source records: `2406`
- rule gaps: `0`
- keyword conflicts: `0`

This final run is the authoritative merge-readiness evidence.

## Temporary workflow cleanup

The one-shot offline ranking workflow and trigger were removed after evidence capture. They never referenced a provider secret.

## Boundaries

- paid model call: `false`
- Registry write: `false`
- website write: `false`
- scheduled: `false`
- published: `false`
- no new atom enabled in this PR
