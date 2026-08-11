from __future__ import annotations

from datetime import datetime, timezone

from .dedup import duplicate_candidates
from .site_contract import required_content_format
from .store import append_jsonl, iter_registry


def known_article_ids() -> set[str]:
    return {row.get("article_id") for row in iter_registry("articles") if row.get("article_id")}


def get_article_record(article_id: str) -> dict | None:
    for row in iter_registry("articles"):
        if row.get("article_id") == article_id:
            return row
    return None


def reserve_blueprints(blueprints: list[dict]) -> dict:
    """Persist non-duplicate ready blueprints as `idea` records."""
    existing_ids = known_article_ids()
    reserved = []
    skipped = []
    for bp in blueprints:
        article_id = bp.get("article_id")
        if not article_id:
            skipped.append({"blueprint_id": bp.get("blueprint_id"), "reason": "missing_article_id"})
            continue
        if article_id in existing_ids:
            skipped.append({"article_id": article_id, "reason": "already_reserved"})
            continue
        if bp.get("status") != "ready_for_draft":
            skipped.append({"article_id": article_id, "reason": f"not_ready:{bp.get('status')}"})
            continue
        if not bp.get("site_category_key") or not bp.get("content_type"):
            skipped.append({"article_id": article_id, "reason": "missing_site_contract"})
            continue
        hits = duplicate_candidates(bp)
        if hits:
            skipped.append({"article_id": article_id, "reason": "duplicate", "hit": hits[0].article_id})
            continue
        record = {
            "article_id": article_id,
            "blueprint_id": bp.get("blueprint_id"),
            "provider_id": bp.get("provider_id"),
            "title": bp.get("title"),
            "slug": bp.get("slug_seed"),
            "primary_keyword": bp.get("primary_keyword"),
            "secondary_keywords": bp.get("secondary_keywords", []),
            "search_intent": bp.get("search_intent"),
            "information_gain_type": bp.get("information_gain_type"),
            "lottery": bp.get("lottery"),
            "play": bp.get("play"),
            "subject_lottery": bp.get("subject_lottery") or bp.get("lottery"),
            "subject_play": bp.get("subject_play") or bp.get("play"),
            "content_type": bp.get("content_type"),
            "site_category_key": bp.get("site_category_key"),
            "content_format": required_content_format(),
            "technique_family": bp.get("technique_family"),
            "technique_atoms": bp.get("technique_atoms", []),
            "angle_signature": bp.get("angle_signature"),
            "case_structure": bp.get("case_structure"),
            "case_scope": bp.get("case_scope"),
            "rule_refs": bp.get("rule_refs", []),
            "source_refs": bp.get("source_refs", []),
            "fingerprint": bp.get("fingerprint"),
            "status": "idea",
            "content_hash": None,
            "published_url": None,
            "published_at": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        append_jsonl("articles", record)
        existing_ids.add(article_id)
        reserved.append(article_id)
    return {"reserved": reserved, "reserved_count": len(reserved), "skipped": skipped, "skipped_count": len(skipped)}


def append_article_state(article_id: str, status: str, changes: dict | None = None) -> dict:
    """Append a lifecycle state update while preserving the article's identity fields."""
    current = get_article_record(article_id) or {"article_id": article_id}
    updated = dict(current)
    updated.update(changes or {})
    updated["article_id"] = article_id
    updated["status"] = status
    updated["updated_at"] = datetime.now(timezone.utc).isoformat()
    append_jsonl("articles", updated)
    return updated
