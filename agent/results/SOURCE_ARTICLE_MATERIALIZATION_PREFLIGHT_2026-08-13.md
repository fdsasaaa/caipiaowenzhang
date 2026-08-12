# Source Article Materialization — Preflight

**Date:** 2026-08-13  
**Status:** IMPLEMENTED — ordinary CI pending

## Why this layer is required

The existing BRBCW import and V2 intelligence pipelines intentionally preserve metadata, hashes, extracted atoms and claims, but do not keep the complete original article body in Git.

That is sufficient for broad family provenance such as `group3_group6`, but insufficient for source-owned parameter binding such as:

- did the original article explicitly say `组三` or `组六`?
- which exact `胆码` term and parameter phrase appeared?
- was a number/window/threshold actually stated by the source or later introduced by the system?

The repository already reserved:

- `knowledge/source_articles/`
- `knowledge/source_manifests/`

This phase turns those reserved directories into an immutable evidence layer for future collected source files.

## Raw-source rule vs reader rewrite rule

This distinction is mandatory:

### Raw source layer

The materialized source snapshot preserves the collected article body **exactly**.

If the source says `时时彩`, the source snapshot keeps `时时彩`.

It must not be rewritten to `分分彩`, because changing the evidence copy would destroy our ability to prove what the source actually said.

### Reader-facing article layer

Downstream generated/re-written articles whose public subject is `分分彩` continue to prefer `分分彩` under the already-accepted reader terminology policy.

Therefore:

> source evidence stays original; reader copy is modernized downstream.

The two layers must never be conflated.

## Materialized source record

For each accepted input article, the tool plans/writes:

`knowledge/source_articles/<source_id>.json`

For BRBCW numeric thread ids, the canonical id remains:

`BRBCW-000001`, `BRBCW-004115`, etc.

Each snapshot stores:

- schema version;
- source id / source name / native id;
- source URL;
- title;
- classification;
- published_at when available;
- exact article body in `content`;
- SHA256 of the exact body;
- body length;
- literal exact-term index;
- explicit raw-source preservation policy;
- non-publishable verification status.

## Literal term index

The materializer records literal occurrences only; it does not infer hidden parameters.

Indexed terms include:

- group3 literals: `组三 / 组选3 / 组选三`;
- group6 literals: `组六 / 组选6 / 组选六`;
- dan literals: `胆码 / 定胆 / 定码`;
- count of raw `时时彩` occurrences;
- count of raw `分分彩` occurrences.

Character offsets are preserved for exact literal matches.

The index does **not** invent a `candidate_digit_set` from nearby digits. A source that merely says `胆码` remains insufficient for executable dan semantics.

## Immutability rule

A materialized `source_id` is an evidence snapshot.

If the same source id is imported again:

- same exact content SHA256 → idempotent `unchanged`;
- different content SHA256 → hard `conflict`;
- existing evidence is not silently overwritten.

If a source genuinely needs a new snapshot/version, it must be represented explicitly rather than mutating old evidence in place.

## Dry-run-first CLI

Command:

`python scripts/materialize_source_articles.py <input>`

Default behavior is dry-run only.

To write snapshots and the manifest:

`python scripts/materialize_source_articles.py <input> --apply`

Supported input types inherit the existing source reader:

- JSON
- JSONL
- CSV
- Parquet

The tool writes a compact manifest to:

`knowledge/source_manifests/materialized_sources.jsonl`

The manifest contains hashes/paths/counts, not duplicate full article bodies.

## Provenance integration proof

The regression suite demonstrates the future intended flow using synthetic source text only:

1. materialize a synthetic `BRBCW-004115` source whose exact body contains `组六`;
2. point the already-existing `source_exact_phrase` group-mode binder at that materialized source directory;
3. bind `FAM-f8efc151837be787` to group6;
4. confirm mode owner becomes `source` and exact matched term contains `组六`.

Inverse test:

- if the materialized source says only broad `组选` and never explicitly says 组六, source-owned `group6` binding still fails.

This proves the new layer can close the provenance gap **once the user's collected original articles are supplied**, without guessing or scraping them again.

## What this PR does not do

- does not scrape BRBCW;
- does not materialize any real article yet because no collected full-text input file is currently present in `knowledge/source_articles/`;
- does not rewrite raw `时时彩` to `分分彩`;
- does not infer dan digits;
- does not enable `dan_candidate`;
- does not make `group3_group6` globally executable;
- does not call a model;
- does not write Registry/site drafts;
- does not schedule or publish.

## Next gate after CI

Once ordinary CI passes, this materialization capability should be merged and left ready for the user's collected article files.

When the first real collected batch is available, the correct workflow is:

1. dry-run materialization;
2. inspect rejected/conflict counts;
3. apply immutable snapshots;
4. run repository audit and exact-phrase diagnostics;
5. only then upgrade source-owned group/dan parameter bindings where the original evidence actually supports them.
