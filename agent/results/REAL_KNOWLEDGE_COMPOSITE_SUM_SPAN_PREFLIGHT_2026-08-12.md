# Real Knowledge Cross-Family Composition — Sum + Span

**Status:** ACCEPTED — offline two-source composition is deterministic and source boundaries remain explicit  
**Date:** 2026-08-12

## Why this architecture exists

The complete 759-family feasibility scan proved that the current archive has zero additional families that independently satisfy the strict 2–3 deterministic-atom matrix contract. It did identify two source-backed single-atom families that can both be placed in the same verified 后三 ordered candidate space.

This phase therefore validates the next evidence-backed architecture:

> independent source family A + independent source family B → explicitly system-authored multistage composition.

The composition itself is **not** attributed to either source.

## Source family A — sum

- family: `FAM-c7549b61f340ef66`
- family atoms: `position_filter + sum_range`
- executable atom used here: `sum_range`
- source: `BRBCW-006020`
- source support: `30`
- source risk: `0.400`
- archive position mask includes `后三`

This source family supports only the presence/provenance of the `sum_range` atom in the family archive.

## Source family B — span

- family: `FAM-c93cfcc1527bf6f8`
- family atoms: `position_filter + span_range`
- executable atom used here: `span_range`
- source: `BRBCW-002590`
- source support: `29`
- source risk: `0.379`
- archive position mask includes `后三`

This source family supports only the presence/provenance of the `span_range` atom in the family archive.

## Common experimental candidate space

Both families are experimentally bound to:

- play: `后三直选`
- verified mechanics: `SSC-HIST-MECH-3STAR-LAST-V1`
- ordered space: `000–999`
- starting candidates: `1000`

The play binding remains:

`archive_position_mask_experimental_binding_not_source_play_claim`

The cross-family combination remains:

`system_authored_cross_family_composition_not_source_claim`

## Frozen system research path

The stage order and numeric parameters are system research choices frozen before any example/sample is inspected:

1. `sum_range`, preset `8–19`
2. `span_range`, preset `3–7`

Exact machine path:

- `1000 → 760` after sum layer; exclude `240`
- `760 → 534` after span layer; exclude `226`
- final: `534`
- total excluded: `466`

This is candidate-space arithmetic only. It is not evidence that the combined method predicts future draws or improves profitability.

## Order is part of the experiment

Reversing the same two predicates can lead to the same final set but a different intermediate path:

- frozen order: `sum → span` = `1000 → 760 → 534`
- reversed order: `span → sum` = `1000 → 690 → 534`

Therefore stage order is locked as system-owned experimental metadata. A later article must not imply that either archived source prescribed this order.

## Candidate-set integrity

The final set contains `534` ordered three-digit candidates. Rather than storing a large manually copied list as the primary integrity mechanism, the preflight locks both exact count and deterministic SHA256 over newline-delimited candidate strings:

`20e0d1759e51aea0e10d93eb3ccb71af5a2aa5ec659ca72fc8d856cb16a9fa95`

Tests also preserve first/last candidate previews for human inspection.

## Ordinary CI acceptance

GitHub Actions run:

- workflow: `test`
- run: `31610203863`
- branch head at test: `809aec23d5a6d5cefcb2ec6dc0bbe00113d473c4`
- Python 3.10: `success`
- Python 3.13: `success`
- repository audit: `pass`
- registry articles: `8`
- registry sources: `2406`
- rule gaps: `0`
- keyword conflicts: `0`
- Python 3.10 pytest: `307 passed`

The regression suite verifies not only the expected path but also the negative cases: changing the pre-frozen sum parameter alters the locked path, and reversing stage order produces `1000 → 690 → 534` rather than the accepted `1000 → 760 → 534`.

No paid provider workflow or API secret is involved in this acceptance.

## Safety boundaries

- paid model call: `false`
- Registry write: `false`
- website draft write: `false`
- scheduled: `false`
- published: `false`
- article generation: `false`

This PR establishes only the deterministic cross-family composition contract. The next justified step is an offline article-generation contract that teaches the model how to explain the two independent source families without falsely presenting the composition, stage order, or numeric thresholds as source-authored.