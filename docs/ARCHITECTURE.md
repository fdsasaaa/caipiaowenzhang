# Architecture

## Three-layer design

1. **Content Engine — this repository**
   - rules
   - source manifests
   - technique atoms
   - article registry
   - quality and duplicate gates
   - approved drafts

2. **Publishing Bridge — website repository**
   - transforms approved drafts into site/WordPress format
   - validates category, slug, metadata, internal links
   - places content in draft/queue

3. **Production — laocaimi.org server**
   - serves pages
   - runs only the minimum publishing/runtime components

## Canonical vs rebuildable state

Canonical in Git:
- `rules/**/*.json`
- `knowledge/source_manifests/*.jsonl`
- `registry/*.jsonl`
- approved/published article markdown/json

Rebuildable local state:
- `var/index.sqlite3`
- similarity caches
- reports

## Future extensions

- official/platform rule adapters
- semantic embeddings for duplicate detection
- Search Console feedback ingestion
- publishing API adapter
- multi-site output while sharing one knowledge base
