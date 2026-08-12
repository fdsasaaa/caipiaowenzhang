# Formal Approved Package Inventory

`articles/approved/` is the canonical future cross-repository transport inventory for `fdsasaaa/xyptdq`.

It is deliberately different from:

- Registry lifecycle state (`registry/articles.jsonl`);
- per-run artifacts such as `runs/.../<article_id>/approved.json`;
- website Draft state;
- Scheduled or Published state.

## Stage one already-approved package

```bash
python scripts/stage_formal_approved_package.py \
  --input runs/batch-001/<article_id>/approved.json
```

This validates the package and atomically writes:

```text
articles/approved/<article_id>.json
```

It does not contact the website, create `publish_at`, schedule content or publish anything.

## Produce and stage a single article

```bash
OPENAI_API_KEY=... \
python scripts/generate_and_review_v2.py \
  --packet packet.json \
  --draft-output draft.json \
  --report-output review.json \
  --approved-output approved.json \
  --record \
  --stage-approved
```

`--stage-approved` is explicit. Without it, Approval can succeed without changing the formal inventory.

## Produce and stage a batch

```bash
OPENAI_API_KEY=... \
python scripts/produce_ranked_batch_v2.py \
  --provider <provider_id> \
  --lottery 时时彩 \
  --play 后三直选 \
  --count 5 \
  --output-dir runs/batch-001 \
  --record \
  --stage-approved
```

Each successful Approved Package is still written to its run folder for evidence. With `--stage-approved`, it is also staged into the canonical inventory.

## Safety and idempotency

Formal staging requires:

- `status=approved`;
- valid stable `article_id`;
- non-empty content;
- required `content_hash` exactly matching content bytes;
- required fingerprint;
- `content_type` and `site_category_key` matching the website contract;
- valid optional SEO cluster metadata.

Behavior for an existing `article_id`:

- exact same Approved Package → `unchanged`;
- different `content_hash` → reject; revision + re-Approval path required;
- same content hash but different approved metadata → reject; an explicit approved-inventory revision path is required rather than silent overwrite.

This prevents a later batch from silently replacing an already staged formal package.

## Publication boundary

Formal inventory staging is **not** publication authorization.

The website contract still separately requires:

```text
Formal Approved Package
  -> future cross-repo transport (currently disabled)
  -> website Draft
  -> explicit scheduling
  -> Native Publisher
  -> Publication Receipt
```

At the time this feature was introduced, cross-repo sync remained disabled and website article publishing remained frozen.
