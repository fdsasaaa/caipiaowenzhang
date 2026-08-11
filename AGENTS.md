# AGENTS.md

## Scope
These rules apply to the entire repository.

## Engineering rules
- `main` is the formal source of truth.
- Prefer changes through a feature branch + PR once the repository is bootstrapped.
- Keep canonical registries in JSONL; SQLite under `var/` is a rebuildable local index and must not be treated as the source of truth.
- Do not commit secrets, API keys, WordPress passwords, cookies, or session tokens.
- Do not commit scraped full-text corpora while this repository is public.
- All rule records must carry provenance and verification status.
- New generators/validators require tests.

## Content rules
- Never claim guaranteed profit, guaranteed hit rate, or risk-free betting.
- Distinguish platform rules from source claims.
- Every published article must have a unique `article_id` and fingerprint.
- Do not approve a draft if its core technique duplicates a published/approved article.
