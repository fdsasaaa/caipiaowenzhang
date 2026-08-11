# Editorial / Practical Quality V2.1

V2.1 separates machine correctness from reader usefulness.

## Two scores

- `quality_score`: hard correctness, rule/evidence/compliance/dedup quality.
- `editorial_score`: whether a reader can actually reproduce the method and knows where to stop.

A new V2.1 article must pass both.

## Practical guidance contract

New blueprints default to `editorial_contract_version=1.0` unless the same article already exists in Registry as a legacy object.

Generated articles must provide:

- `steps`: at least four concrete operations;
- `starting_space`: candidate space before the main filter;
- `after_primary_filter_space`: candidate space after the main filter;
- `parameter_freeze_rule`: parameters are fixed before observing the evaluation sample;
- `stop_condition`: if no second validated and reproducible rule exists, stop adding filters;
- `next_step_policy`: any extra filter requires verified rule/evidence and a reproducible algorithm.

The body must contain a visible practical-operation section. For filter-style articles, when candidate-space size is computable, V2.1 checks that the primary filter actually reduces the space.

## Why the stop rule exists

The purpose is not to force every article to combine multiple techniques. Adding a second condition only to make the article look more actionable creates post-hoc rules and raises overfitting risk. A high-quality article is allowed to stop after one filter when that is the last verified step.

## Backward compatibility

Existing V2.0 articles in Registry do not automatically inherit the V2.1 editorial contract. Reconstructing their Blueprint preserves their legacy lifecycle unless they are explicitly revised under the newer contract.

## Baseline quality smoke

`agent/results/v2-quality-smoke-001/` is the first V2.1 human-review baseline. It studies a source-suggested last-three sum range of 10–17 by:

1. validating the ordered last-three mechanics;
2. enumerating all 000–999 outcomes;
3. proving that sums 10–17 cover 560 outcomes and remove 440;
4. applying the fixed range to deterministic synthetic data;
5. stopping instead of inventing an unverified second filter.

The baseline is a repository quality fixture only. It is not automatically registered, scheduled, or published.
