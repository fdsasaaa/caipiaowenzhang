# Creator-first Slim Architecture

## Core decision

The model is the primary creator. The repository is the validator and long-term memory.

The default creation path no longer starts by enumerating a finite article candidate pool or assigning a mandatory article-angle contract. Those systems remain available for legacy batch research, but they no longer define what the model is allowed to invent.

## Highest-level goal

Continuously create large numbers of useful, non-duplicate lottery articles across:

- different games and play types;
- different technique ideas;
- different combinations of methods;
- different explanation styles and case designs;
- bankroll/risk-management research;
- staking/progression research;
- future draw-data research when a proper draw-data evidence channel is connected.

Reader copy should be simple, concise and human. It should not expose repository engineering concepts or read like a generated factory report.

## The new default flow

```text
GitHub memory + verified gameplay mechanics
            ↓
      AI freely creates ONE idea
            ↓
 AI writes creative brief + article in one request
            ↓
      Existing hard validators
   ├─ verified mechanics
   ├─ Claim → Evidence
   ├─ bet compliance
   ├─ lexical / structural dedup
   ├─ SEO keyword ownership
   ├─ reader terminology
   ├─ human-style gate
   └─ formal-inventory integrity
            ↓
      Approved Package / GitHub memory
```

There is no mandatory Planner → finite candidate pool → angle assignment step in this path.

## What the AI owns

The creator may decide:

- which verified play to write about;
- the technique idea;
- whether to use one method or several;
- whether the article is a technique, data-research, bankroll, staking or hybrid article;
- the explanation structure;
- the example design;
- the SEO wording;
- when a simple article is better than a complicated article.

Existing source articles and prior Approved articles are memory and inspiration only. They are not mandatory templates.

## What the system still owns

The system is intentionally narrow but strict.

It still blocks:

- a play with no verified mechanics;
- fabricated rule refs or source refs;
- unsupported platform odds/prize/rebate facts;
- guaranteed-profit or guaranteed-hit language;
- executable betting examples that violate the compliance policy;
- unregistered hard claims;
- duplicate/near-duplicate articles;
- reader-facing legacy `时时彩` terminology when the public subject is `分分彩`;
- internal engineering jargon leaking into reader copy;
- invalid Approved Package / Registry writes.

These gates judge the output. They do not decide the creative idea in advance.

## Bankroll and staking articles

Creator-first explicitly allows bankroll and staking/progression research.

When provider economics are not verified:

- prefer relative stake units rather than pretending a platform payout is known;
- explain maximum exposure, drawdown, stop conditions and sequence behavior;
- do not claim that progression turns a negative/unknown game into guaranteed profit;
- specific payout/rebate economics remain blocked unless verified separately.

This lets the model create rich money-management content without fabricating platform facts.

## Historical draw data

Creator-first V1 deliberately starts with `draw_data_available=false` because the current generic Claim→Evidence vocabulary does not yet distinguish verified historical draw datasets from self-authored synthetic examples.

This is not a return to a complex planner. A future extension only needs one additional input/evidence channel:

```text
verified draw-data file → creator context → model-created technique → same validators
```

The creative architecture does not need to change.

## Human style

Reader-facing articles should not contain internal terms such as:

- Draft Packet
- Blueprint
- angle_delivery
- claim_evidence
- provider_response_id
- candidate_capacity
- system_research
- machine/engineering contract language

The style gate is intentionally small. It does not prescribe a fixed outline, fixed number of sections, or fixed writing template.

## Legacy components

The following capabilities remain in the repository for compatibility, research and optional batch use:

- Planner
- Article Angle Contract
- candidate-capacity preplanning
- V2.2 multistage filter contracts

They are no longer the conceptual default for article creation.

No destructive deletion is required for the first slimming phase. After creator-first passes real canary tests, unused legacy paths can be moved behind explicit `--legacy-*` entry points or archived in a later cleanup PR.

## Production discipline

Creator-first V1 is intentionally one article at a time:

- one request;
- no automatic retry;
- validation after generation;
- only an approved result may be staged;
- no website sync, scheduling or publication.

Once real acceptance is stable, repeated creation means calling the same simple loop again with updated GitHub memory. The model is expected to create the next idea from what it already knows plus the accumulated memory, rather than consuming a pre-enumerated finite pool.
