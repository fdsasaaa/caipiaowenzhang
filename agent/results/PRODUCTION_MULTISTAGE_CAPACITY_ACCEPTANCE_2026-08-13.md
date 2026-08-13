# Formal Article Production — Strict Multistage Capacity Acceptance

**Date:** 2026-08-13  
**Status:** ACCEPTED — target 200 feasible without lowering gates  
**Provider calls in this phase:** 0

## Why this correction was required

The previously merged production primary-filter contract proved that formal candidates could bind a machine-computable first filter before provider generation, but two semantic gaps remained:

1. a multi-atom article could still execute only one atom while title/SEO exposed multiple method labels;
2. frequency/cold/hot/omission resolved digit pools were derived from synthetic sample data but could be described too loosely as fully pre-frozen parameters.

Those gaps would inflate apparent content capacity and create articles whose reader-facing method labels were not fully executed.

This correction keeps the production target at 200 but requires every reader-facing method atom to map to a real, auditable machine stage.

## All-method execution rule

For formal production, all non-context method atoms must be covered by the production contract.

Context only:

- `position_filter`

Supported static method stages:

- `sum_range`
- `span_range`
- `big_small_filter`
- `odd_even_filter`
- `repeat_number`
- `neighbor_number`

Supported sample-rule stages:

- `cold_hot_split`
- `frequency_window`
- `omission_threshold`

Unsupported atoms remain fail-closed.

Every stage must:

- have a defined candidate domain;
- make a strict non-empty reduction;
- preserve source/system parameter ownership;
- declare its evidence support mode;
- avoid any predictive-advantage claim.

If a later method becomes a no-op or empties the candidate set, the entire article candidate is blocked before provider generation. It is not allowed to remain in SEO/title while being silently ignored.

## Multistage routing

Single-stage production articles continue through the ordinary structured generator and standard Approval stack.

Multi-stage production articles now:

1. receive `contract_version=2.2-multistage`;
2. receive complete `filter_pipeline_spec` and machine-enumerated `filter_pipeline_result`;
3. use the V2.2 multistage generation prompt;
4. must execute all contract stages in the frozen system order;
5. pass `evaluate_multistage` **before** standard Approval;
6. cannot be staged into formal inventory after a failed multistage gate.

Custom generator injection used by tests remains higher priority than the default route, so existing controller testability is preserved.

## Static vs sample-derived evidence

### Static stages

Static stage parameters are system research presets and are machine-enumerated against verified gameplay spaces.

Stage calculation evidence:

- support type: `verified_rule`
- support refs: the Draft Packet `rule_refs`

### Sample-derived stages

For frequency/cold/hot/omission stages, the contract explicitly separates two concepts:

**Frozen before observation:**

- lookback/window length;
- ranking rule;
- top-N policy;
- omission threshold/comparison rule.

**Calculated from deterministic synthetic case data:**

- the exact selected digit pool;
- the resulting candidate-space counts.

These stages therefore use:

- support type: `synthetic_case`
- support refs: `["case_bundle"]`
- `resolved_parameters_derived_from_synthetic_case=true`
- `parameter_freeze_before_observation=false`

The system must not claim that the exact sample-derived digits were known before the sample was evaluated.

If any pipeline stage depends on synthetic-case-derived parameters, the overall pipeline final-space calculation is also classified as `synthetic_case` rather than letting a gameplay rule stand in for sample evidence.

## Cold/hot + frequency-window compound stage

`cold_hot_split` and `frequency_window` refer to the same sample frequency ranking/window when they co-occur in one family. Executing the same digit pool twice would create a fake second stage with zero reduction.

The production contract therefore represents the pair as one compound, auditable stage:

`cold_hot_frequency_window`

That one stage covers both reader-facing atoms while preserving one actual sample-derived digit pool.

## Fixed Top-5 production frequency policy

The strict Top-3 contract produced only `187` globally deduplicated candidates, which was below the requested 200 target.

The dominant block reason was not missing mechanics; it was that a Top-3 frequency pool was too narrow to coexist with legitimate later/earlier filters and frequently produced an empty intersection.

The production research policy is therefore fixed to:

- sample lookback: as supplied by the deterministic case bundle (currently 12);
- rank digits by sample frequency descending;
- tie-break by digit ascending;
- retain Top-5 digits (`PRODUCTION_FREQUENCY_TOP_N=5`).

Rationale: Top-5 retains half of the 0–9 digit universe as an intermediate frequency/cold pool, leaving room for later independent filter stages. This is an engineering/research-domain policy, **not** a claim that Top-5 predicts better or improves hit rate.

When the full 0–9 frequency table is available, production ignores the historical helper's pre-resolved Top-3 list and recomputes its own Top-5 pool from the full table.

The rule is fixed before article generation; the exact five digits are still calculated from the deterministic synthetic case and are not source-selected or pre-known.

## Capacity history

### Strict Top-3 all-method scan

Run: `31652569945`

Result:

- target: `200`
- strict candidate capacity: `187`
- single-stage: `86`
- multistage: `101`
- exhaustive: `true`
- target feasible: `false`
- provider calls: `0`
- artifact id: `9163136177`
- artifact SHA256: `c8773b07ede4a7ca4ae18d70ddef3950a725cbee75e5a92ba3ca056b525dca3a`

This result is important because it proves the system did **not** keep the earlier inflated `227` capacity by ignoring reader-facing methods.

### Block diagnostic

Run: `31652713477`

The strict diagnostic confirmed that most blocked contracts came from:

- frequency/cold Top-3 stages producing empty intersections with other legitimate stages;
- a smaller number of later-stage no-ops/empty results;
- a few categorical `后二大小单双` candidates that still lack a numeric production-domain contract.

No blocked no-op/empty candidate was restored merely to reach the target.

### Accepted strict Top-5 scan

Authoritative capacity run: `31653193782`

Result:

- target: `200`
- candidate capacity: `216`
- single-stage: `86`
- multistage: `130`
- exhaustive: `true`
- target feasible: `true`
- capacity probe passes: `2`
- attempt budget: `216`
- formal inventory before: `0`
- provider calls: `0`
- website sync: `false`
- scheduling: `false`
- publishing: `false`
- artifact id: `9163355576`
- artifact SHA256: `994a4dd460421af3df0d8798f09b04fc778d38fa3637a625ab28fa1c217bef1e`

The increase from `187` to `216` comes from the single uniform Top-5 intermediate frequency policy. It does not re-enable no-op or empty-stage contracts.

## CI evidence

Authoritative ordinary merge-ref CI for the accepted Top-5 executable state:

- run: `31653196290`
- merge ref tested: `e8d61dbe7af05044cd629d7a5577c328d593a9b8`
- PR head tested: `5a56e6d593b1d3317a583cdf106246c00ca62275`
- main tested: `6f46295eea6adca1d232c9a3de9f69b3c9e2cc1a`
- Python 3.10: SUCCESS
- Python 3.13: SUCCESS
- repository audit: PASS
- pytest: `426 passed`
- registry articles: `8`
- source records: `2406`
- rule gaps: `0`
- keyword conflicts: `0`

Subsequent branch commits only remove the temporary offline capacity workflow/trigger and add this acceptance record; production executable code is unchanged from the merge-ref-tested state.

## Temporary workflow cleanup

The offline capacity workflow and trigger were removed after evidence capture:

- `.github/workflows/production-multistage-capacity-temp.yml`
- `.github/production-multistage-capacity.trigger`

They never referenced provider credentials.

The diagnostic script remains as a normal offline maintenance tool because it can explain future capacity losses without spending provider calls.

## Reader-facing terminology and provenance

All existing reader-facing terminology gates remain in force:

- FFC articles prefer `分分彩`;
- raw/internal historical evidence may retain `时时彩` where technically correct;
- source refs support broad technique-family provenance;
- stage order, static presets and sample-selection rules are system research choices;
- sample-derived exact digit pools are case calculations, not source recommendations.

## Safety boundaries

- provider calls in this acceptance phase: `0`
- formal inventory writes in this acceptance phase: `0`
- Registry writes in this acceptance phase: `0`
- website writes: `0`
- scheduling: `false`
- publishing: `false`
- quality floor lowering: `false`
- no-op stage restoration: `false`

## Next gate

The 200-article target is now mathematically feasible with `216` strict candidates.

The next step is **not** to fire 200 model calls immediately. Create a fresh production branch from the merged main and run one persisted paid canary using the exact production controller path. If that single article passes the correct single/multistage route, standard Approval, terminology audit and formal-inventory commit/push, it counts as article #1 toward the target. Only then scale in controlled batches toward 200.
