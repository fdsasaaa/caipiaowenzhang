# Hub Readiness Audit

This audit measures formal, transportable Approved Package coverage by explicit SEO cluster metadata. It does **not** create Hub pages and it does **not** decide that a Hub is ready automatically.

## Why this exists

The article Registry and `articles/approved/` represent different things:

- `registry/articles.jsonl` is append-only lifecycle memory with last-write-wins semantics.
- `articles/approved/*.json` is the future cross-repository transport inventory.

An article with Registry status `approved` is not automatically a transportable Approved Package file. Hub planning must not confuse those two states.

## Run

```bash
python scripts/audit_hub_readiness.py
```

The report includes:

- formal Approved Package file count;
- explicit primary/secondary SEO cluster coverage;
- unassigned formal packages;
- effective Registry approved count as a separate informational number;
- validation errors;
- per-cluster coverage.

## Cluster coverage is not Hub readiness

A cluster with formal package coverage receives only:

`formal_package_coverage_present_editorial_review_required`

The audit intentionally never returns automatic Hub readiness. A real Hub still requires:

1. substantive supporting content;
2. a distinct primary search intent;
3. useful Hub copy and navigation;
4. real internal-link targets;
5. a verified live URL;
6. HTTP 200 and self-canonical checks before sitemap/Keyword Map ownership changes.

## Current checkpoint

At the time this audit was introduced, `articles/approved/` contains only `.gitkeep`, so the formal transport inventory is **0 packages**. The Registry still contains historical/smoke articles whose effective lifecycle state is `approved`; those records must not be counted as formal cross-repository inventory.

This distinction is deliberate and prevents smoke-test state from being mistaken for publication-ready corpus size.
