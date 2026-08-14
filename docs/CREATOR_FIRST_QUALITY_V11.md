# Creator-first V1.1: Quality Memory Layer

## Status

This is a thin, additive quality layer on top of Creator-first V1. It does not replace the existing Approval system, does not lower duplicate thresholds, and does not add website publication side effects.

## Stable rollout

- Stable V1 fallback: `scripts/create_article.py`
- Recommended V1.1 quality entry: `scripts/create_article_quality.py`

The V1 fallback is intentionally retained. Do not delete it until V1.1 has enough production canaries. This gives the project an immediate rollback path without reverting repository history.

## What V1.1 adds

### 1. Long-term creative memory

V1.1 dynamically reads formal approved inventory from `articles/approved/*.json` plus active Registry records. It does not maintain a second persistent memory database.

The memory snapshot contains compact coverage information only: play counts, technique atoms, coverage signatures and a bounded set of representative articles. Existing articles are memory for avoiding repetition, never templates to imitate.

### 2. Formal-inventory duplicate gate

After the existing Creator-first Approval and human-style checks pass, V1.1 compares the candidate with the complete formal approved inventory using the existing lexical and structural similarity functions and unchanged thresholds.

This closes the gap where formal JSON inventory can be larger than Registry memory.

### 3. Soft Style DNA

Each request receives one deterministic Style DNA selected from multiple writing tendencies such as case-first, question-first, research-note, comparison, calculation-first and minimal tutorial.

Style DNA is soft guidance only. It must never become a fixed article template or override clarity, correctness or verified gameplay mechanics.

### 4. Multi-title selection guidance

The model is instructed to internally consider at least five materially different title directions and output only the final winner. Selection balances accuracy, natural SEO fit, reader curiosity, distinctness and non-exaggeration.

### 5. Technique learning metadata

When a V1.1 article passes all gates, its formal package is enriched with compact creator memory metadata:

- `creator_style_id`
- `creator_novelty_summary`
- `creator_technique_memory`

Future memory can therefore reuse successful ideas as knowledge while still treating them as anti-duplication memory rather than templates.

## What V1.1 deliberately does not do

- no Planner reactivation
- no Article Angle requirement
- no finite candidate-capacity worldview
- no automatic retry
- no lower Approval or duplicate threshold
- no draw-data claim when draw data is absent
- no website sync
- no scheduling
- no publication
- no inline visual-design system; website owns typography, colors and layout

## Stability rule

If V1.1 fails or produces an undesirable result, use `scripts/create_article.py` immediately. V1 remains intact and tested.

The project principle remains:

**AI creates; repository validates and remembers; website presents.**
