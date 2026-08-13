# Audited Article Angle Contract V1 — Acceptance Record

Date: 2026-08-13
Repository: `fdsasaaa/caipiaowenzhang`
Scope: formal article-production identity, deduplication, Draft Packet, generation schema, Approval, and sustainable production capacity
Provider calls in this engineering acceptance: **0**
Website sync / scheduling / publishing: **disabled / disabled / disabled**

## 1. Why this change was necessary

The strict V6 production branch already had one accepted formal canary (`1/200`). A zero-provider sustainable-capacity scan proved that the old production identity was not capable of safely supporting the remaining campaign:

- run: `31657446385`
- artifact: `9164908982`
- artifact SHA256: `b2839160143c84c34f531ccd77e9216fa559bff3679f3dd130cf2f5c5379151a`
- raw strict candidates after the accepted canary: `214`
- current-Registry duplicate blocks: `0`
- sustainable intra-pool conflict-free sequence under the existing thresholds: **38**
- blocked by intra-pool conflicts: `176`
  - lexical: `171`
  - structural: `5`

The thresholds were and remain:

- lexical duplicate threshold: **0.72**
- structural duplicate threshold: **0.82**

The conclusion was that the old candidates were not 214 genuinely distinct pages. Most were the same `method mechanics + reproducible case` document identity with small play/window substitutions.

This also matched the earlier stale V4 paid-batch evidence: the batch attempted 66 / generated 65; 54 failed Approval, 52 of those contained duplicate-risk failures, and 40 had duplicate risk as the only Approval failure. Duplicate detection therefore had to be solved before further paid scale-up.

## 2. Rejected approaches

The following were explicitly rejected:

1. lowering lexical `0.72` or structural `0.82` thresholds;
2. treating a different play/window as an automatic duplicate exemption;
3. changing titles or search-intent wording merely to lower similarity;
4. assuming `2406` source records represent `2406` independent full-text articles;
5. restoring no-op / empty / unprovable filter candidates merely to reach 200.

`knowledge/source_articles/` remains without a materialized full-text corpus in the current mainline, so source count was not used as a false capacity multiplier.

## 3. Zero-provider research sequence

### 3.1 Wording-only identity changes were insufficient

Run `31657854913`, artifact `9165054335`, SHA256 `88defff3ce27924e82e72b5e7d5f6b876383eb58f9a281619a90d996b22139b8`:

- baseline sustainable capacity: `38`
- machine-specific title + search intent: `49`
- plus real pipeline identity: `57`
- reader-task wording contract: `49`

Therefore ordinary copy differentiation was rejected as an architecture fix.

### 3.2 Genuine information-gain variants

Run `31658183617`, artifact `9165187523`, SHA256 `852b4e4bb0021f138abcbadc789001fc75b6452db5f5ce37e3e4187fd769455d`.

Six information-gain tasks were researched:

- `mechanics_case`
- `space_math`
- `execution_checklist`
- `parameter_boundary`
- `multistage_order` — only when the machine contract has at least two stages
- `sample_provenance` — only when the machine contract contains a sample-derived stage

These are not synonym buckets. Each has a different reader question and a different required machine-verifiable deliverable.

Using a research-only 20% audited information-gain structural dimension produced:

- base candidates: `214`
- angle variants: `1111`
- eligible against the current Registry: `1100`
- sustainable greedy sequence: **236** under both tested orderings
- remaining conflicts: `864`
- cross-angle remaining conflicts: **0**
- all remaining conflicts were inside the same information-gain type

### 3.3 Weight sensitivity

Run `31658446017`, artifact `9165300726`, SHA256 `0fdecfe3e8cc6c0cd397c3aea677c48a8877f270caf2de985a26ca917852368a`:

| Audited angle structural weight | Sustainable capacity |
|---:|---:|
| 0% | 130 |
| 10% | 162 |
| 15% | 168 |
| 20% | 236 |
| 25% | 235 |

The 20% choice is not a threshold relaxation and is not a value tuned to barely reach 199. The existing structural threshold is `0.82`; a new independent structural identity dimension must exceed 18% before two otherwise identical machine structures with genuinely different audited reader tasks can fall below the same-document threshold. `0.20` also matches the existing play-family structural weight, and `20% -> 25%` is stable (`236 -> 235`).

## 4. Fail-closed production design

The 20% information-gain dimension applies **only when both records possess a verified V1 article-angle contract**.

For an active formal owner (`approved`, `queued`, `scheduled`, `published`), it additionally requires:

- `article_angle_contract_version == "1.0"`
- recognized information-gain type
- `angle_contract_verified == true`
- `angle_approval_passed == true`

Otherwise the record receives the previous legacy structural score with no angle separation.

For two audited records:

- same audited angle: `0.8 * base_structural_score + 0.2`
- different audited angle: `0.8 * base_structural_score`

For legacy/uncontracted/unapproved-angle records:

- structural score is unchanged from the previous implementation.

Lexical threshold remains `0.72`; structural threshold remains `0.82`.

## 5. Contracted article deliverables

A deterministic `article_angle_contract` is created only after the machine production-filter contract exists. It freezes, among other fields:

- angle type and contract ID;
- primary keyword, title, search intent, reader question;
- required deliverable and outline;
- pipeline signature;
- starting / final / excluded candidate-space counts;
- stage count and ordered stage labels;
- static vs sample-derived stage labels;
- evidence mode;
- `parameter_owner = system_research`;
- source-parameter attribution forbidden;
- predictive-advantage claim forbidden;
- stop after the final contracted stage.

The generation schema requires a structured `angle_delivery` object for contracted articles. The angle quality gate then compares it back to the immutable machine contract and also checks visible article content.

Examples of fail-closed requirements:

- `space_math`: machine start/final/excluded numbers and visible candidate-space calculation;
- `execution_checklist`: concrete ordered steps covering every contracted stage;
- `parameter_boundary`: explicit system/source boundary, and sample-derived distinction where applicable;
- `multistage_order`: all contracted stage labels in the machine order plus machine counts;
- `sample_provenance`: standard synthetic-case disclosure and explicit non-predictive boundary;
- `mechanics_case`: a complete reproducible example, not a generic technique page.

Only a passed contract is persisted into the Approved Package / Registry as audited structural identity.

## 6. Candidate-pool dedup now occurs before provider calls

Production discovery now:

1. builds the machine filter contract;
2. expands only machine-supported article-angle contracts;
3. applies exact keyword ownership and live Registry duplicate gates to each variant;
4. ranks eligible variants;
5. builds an internally conflict-free candidate pool using the existing lexical `0.72` and structural `0.82` thresholds;
6. only then exposes the pool to the provider execution plan.

This turns `candidate_capacity_current_snapshot` into a sustainable conflict-free capacity measure rather than a count of labels that will collide later in the same paid batch.

## 7. Formal implementation acceptance

Zero-provider implementation run:

- run: `31659609053`
- job: `94321468932`
- capacity artifact: `9165702976`
- artifact SHA256: `2b85dea4643996d64250757af5840b470362dae63ac139922a2bc62f23a822c9`
- provider calls: **0**

Regression results:

- targeted article-angle / generation / Approval / dedup / controller tests: **37 passed**
- full offline suite: **450 passed**
- engine audit: PASS
- reader terminology audit: PASS
- Registry: articles=8 / sources=2406
- rule_gaps=0
- keyword_conflicts=0

Formal mainline-state capacity result:

- formal inventory before: `0`
- target: `200`
- sustainable `candidate_capacity_current_snapshot`: **249**
- `capacity_exhaustive=true`
- `target_feasible_current_snapshot=true`
- attempt budget: `249`
- variants blocked inside candidate-pool dedup: **1052**
  - lexical: `971`
  - structural: `81`
- retained contract modes:
  - single-stage: `82`
  - multistage: `167`
- retained angle distribution:
  - mechanics_case: `55`
  - space_math: `72`
  - execution_checklist: `42`
  - parameter_boundary: `37`
  - sample_provenance: `17`
  - multistage_order: `26`
- independent post-plan pairwise duplicate conflicts: **0**

The capacity gain therefore does not come from lowering thresholds. The planner rejected 1052 near-duplicate variants itself and retained 249 that are mutually compatible with the unchanged dedup rules.

## 8. Acceptance boundary

This record accepts the architecture for standard CI / merge-ref validation only.

It does **not** authorize or claim completion of the remaining paid 200-article campaign. Before any next provider request:

1. merge the feature to `main` only after standard Python 3.10 / 3.13 CI is green;
2. merge the validated mainline implementation into V6 while preserving its accepted `1/200` article;
3. rerun zero-provider V6 remaining-target capacity (`199`) on the combined production branch;
4. require conflict-free remaining capacity >= 199 with thresholds still `0.72 / 0.82`;
5. keep website sync, scheduling and publishing disabled.

No provider request was made during this engineering acceptance.
