# 组三 / 组六 / 胆码 Domain Contract

**Date:** 2026-08-13  
**Status:** IMPLEMENTED — ordinary CI pending  
**Mode:** diagnostic only; no new executable atom

## Why this phase exists

The corrected full-archive atom-gap ranking showed that `group3_group6` and `dan_candidate` have substantially more real-archive leverage than the already-understood `neighbor_number`, but neither may be enabled from the compact family label alone.

This phase deliberately separates three kinds of evidence:

1. **verified gameplay mechanics** from the repository rules;
2. **family provenance metadata** from the compact BRBCW family archive;
3. **missing source-specific parameters**, which remain blocked rather than guessed.

## Source archive limitation

The current compact family archive preserves:

- atom mask;
- position mask;
- lottery/class masks;
- source-support count;
- source-risk rate;
- one representative `BRBCW-*` source ref.

It does **not** preserve the exact matched source sentence or bound parameter values for `组三/组六` or `胆码`.

The new `knowledge/source_articles/` directory is currently empty, so this phase does not pretend to have the full original article text.

## Verified 组三 mechanics

Rule: `SSC-HIST-MECH-3STAR-GROUP3-V1`

The verified historical mechanics define 后三组选3 as:

- exactly two of the three digits are equal;
- the third digit is different;
- one unordered multiset `{a,a,b}`, `a != b`, is one group3 bet unit;
- one bet unit covers 3 ordered outcomes.

Machine enumeration therefore locks:

- unordered group3 bet units: `90` (`10 * 9`);
- ordered group3 outcomes in `000–999`: `270` (`90 * 3`).

## Verified 组六 mechanics

Rule: `SSC-HIST-MECH-3STAR-GROUP6-V1`

The verified historical mechanics define 后三组选6 as:

- all three digits are distinct;
- one unordered three-digit set is one group6 bet unit;
- one bet unit covers 6 ordered outcomes.

Machine enumeration therefore locks:

- unordered group6 bet units: `120` (`C(10,3)`);
- ordered group6 outcomes in `000–999`: `720` (`120 * 6`).

## Three-digit multiplicity partition

The full ordered `000–999` space partitions exactly into:

- group3 structure: `270`;
- group6 structure: `720`;
- three identical digits: `10`;
- total: `1000`.

Examples:

- `112`, `121`, `211` → group3;
- `123` → group6;
- `777` → three-identical, neither group3 nor group6.

This partition is a mechanics fact. It does **not** by itself mean a BRBCW family selected 组三 or 组六, and it does not prove predictive advantage.

## Critical domain conclusion

`group3_group6` must **not** be implemented as an ordinary filter over the existing ordered 后三直选 pipeline.

The verified betting domain is different:

- 后三直选 primary units are ordered three-digit outcomes;
- 组三 primary bet units are unordered multisets with multiplicity `2+1`;
- 组六 primary bet units are unordered sets of three distinct digits.

Ordered outcomes may be used for coverage verification, but the betting/candidate unit must remain the correct unordered group unit.

## Why the compact `group3_group6` atom is still blocked

The taxonomy currently maps both `组三` and `组六` to the same canonical atom `group3_group6`. The compact family archive therefore does not tell the execution layer which mode was actually meant.

Required future parameter:

`group_mode = group3 | group6`

Without that parameter, `require_group_mode()` fails closed.

Important real family examples remain non-executable:

- `FAM-f8efc151837be787` → representative source `BRBCW-004115` → `group3_group6 + position_filter`;
- `FAM-7c7feb0b14f7ce5b` → representative source `BRBCW-001195` → `big_small_filter + group3_group6 + position_filter + span_range`;
- `FAM-c9dbf45977248c6b` → representative source `BRBCW-001748` → `dan_candidate + group3_group6 + position_filter`.

The mechanics contract is now available, but these families remain blocked until `group_mode` is bound from a source-specific record or an explicitly declared system-research contract that does not pretend the source chose it.

## Why `胆码` remains more restricted

The taxonomy maps `胆码 / 定胆 / 定码` into `dan_candidate`, but that label alone does not define an executable predicate.

Before a dan-based family can become executable, at minimum the contract must bind:

1. `candidate_digit_set` — which digit(s) are the dan;
2. `containment_or_position_semantics` — must the dan merely occur somewhere, occur at least N times, or appear in a fixed position;
3. `target_play_domain` — ordered direct space, group3 units, group6 units, or another play domain.

Therefore families such as:

- `FAM-dbcf832f1ce7eedc` / `BRBCW-000438`;
- `FAM-418d72a50d4558a4` / `BRBCW-002488`;
- `FAM-c9dbf45977248c6b` / `BRBCW-001748`;

remain fail-closed. The system must not infer generic “contains this digit” semantics merely from the word `胆码`.

## Reader-facing terminology

The public article layer should continue to use `分分彩` wherever practical.

The verified internal mechanics rules retain the historical taxonomy label `时时彩`. This is allowed because it is internal provenance/mechanics metadata and is not rewritten to falsify history.

## What this PR does not do

- does not add `group3_group6` to the executable filter whitelist;
- does not add `dan_candidate` to the executable filter whitelist;
- does not select a group_mode for any source family;
- does not invent dan numbers;
- does not convert group units into direct-bet units;
- does not call a model;
- does not write Registry or website drafts;
- does not schedule or publish anything.

## Next gate after CI

If ordinary CI passes, the next engineering decision should be:

1. create a **parameter-binding contract** for `group_mode` that can distinguish `组三` from `组六` without losing source provenance;
2. only then test one real group family offline;
3. keep `胆码` blocked until full source-specific parameter evidence is available or a separately labelled system-research dan contract is intentionally created.
