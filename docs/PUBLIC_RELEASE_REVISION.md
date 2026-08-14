# Public-release revision contract

Formal Approved inventory is immutable. A website-facing revision must never overwrite `articles/approved/<article_id>.json`.

The public-release layer stores a separately approved derivative under `articles/public_release/<source_batch_id>/` and records an explicit parent relationship.

## Required invariants

- `article_id` remains the source identity.
- `revision_kind` is `website_public_release`.
- `release_revision` is a positive integer and `revision_id` is `<article_id>:public-rN`.
- `parent_content_hash` and `parent_fingerprint` must exactly match the immutable Formal Approved parent.
- Revised content must produce a different `content_hash`.
- `slug`, `primary_keyword`, `site_category_key`, and `content_type` are preserved by default.
- `creator_batch_id` must be preserved from the immutable Formal Approved parent.
- `source_batch_id` must match that same parent `creator_batch_id`; both fields therefore identify the same original production batch while keeping revision-layer provenance explicit.
- `public_release_review.status` must be `approved` and must identify its review contract and review time.
- The revision fingerprint is deterministic over source identity, revision identity, parent identity, content hash, slug, and Primary Keyword.

## Manifest

`write_public_release_manifest()` chooses the latest valid public revision per article. A batch is `complete` only when its validated revision count equals `expected_count`.

- Partial manifests may be used for a controlled canary.
- Full batch ingestion is allowed only when the manifest is complete.
- The manifest is not a publishing authorization. Website scheduling and publication remain separate gates.

## CLI

```bash
python scripts/stage_public_release_revision.py path/to/revision.json --expected-count 50
```

The command stages the revision and rewrites the batch manifest atomically. It never changes the parent Approved Package and never performs website sync, scheduling, or publication.
