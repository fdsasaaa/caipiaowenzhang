# Daily Partial Batch Retention

## Quality-First Policy (v3)

The daily website-ready production follows a quality-first partial batch retention policy:

```text
target = 20
operational_minimum = 10
formal_commit_minimum (minimum) = 1

qualified_count == 0:
    FAIL CLOSED (BLOCKED_BELOW_MINIMUM)
    No inventory committed.

qualified_count 1..19:
    PASS_PARTIAL_QUALITY_FIRST
    All qualified public-r1 articles are retained.
    Operational health signal fires if below operational_minimum.

qualified_count >= 20:
    PASS_TARGET
    Normal target success.
```

## Core Principle

Every article that fully passes all gates (Approval, Quality, Editorial, Dedup,
Keyword Owner, public-r1) is retained. No qualified article is discarded simply
because the batch did not reach a volume threshold.

The `operational_minimum` is a production health signal, not a discard threshold.
When the daily count falls below `operational_minimum`, the system continues
refilling within hard caps, but never discards already-qualified articles.

## Quality Floor

`quality_floor_may_be_lowered = false` means the system never relaxes quality
gates to reach a volume target. Quality always comes first.
