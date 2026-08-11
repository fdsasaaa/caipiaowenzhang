from __future__ import annotations

from .seo_keywords import canonical_primary_keyword
from .store import iter_registry

LINKABLE_STATUSES = {"approved", "queued", "scheduled", "published"}
DEFAULT_MIN_SCORE = 45


def _subject_lottery(record: dict) -> str:
    return str(record.get("subject_lottery") or record.get("lottery") or "").strip()


def _subject_play(record: dict) -> str:
    return str(record.get("subject_play") or record.get("play") or "").strip()


def _play_groups(play: str) -> set[str]:
    groups: set[str] = set()
    if not play:
        return groups
    for token in ("定位胆", "前二", "后二", "前三", "中三", "后三", "组选", "直选", "包胆", "大小单双"):
        if token in play:
            groups.add(token)
    if any(token in play for token in ("前三", "中三", "后三")):
        groups.add("三星")
    if any(token in play for token in ("前二", "后二")):
        groups.add("二星")
    return groups


def _linkable_records() -> list[dict]:
    rows = []
    for row in iter_registry("articles"):
        if row.get("status") not in LINKABLE_STATUSES:
            continue
        if not row.get("article_id"):
            continue
        rows.append(row)
    return rows


def _score(source: dict, target: dict) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    source_lottery = _subject_lottery(source)
    target_lottery = _subject_lottery(target)
    source_play = _subject_play(source)
    target_play = _subject_play(target)

    if source_lottery and source_lottery == target_lottery:
        score += 30
        reasons.append("same_subject_lottery")
    if source_play and source_play == target_play:
        score += 50
        reasons.append("same_subject_play")

    shared_groups = sorted(_play_groups(source_play) & _play_groups(target_play))
    if shared_groups and source_play != target_play:
        group_score = min(30, 15 * len(shared_groups))
        score += group_score
        reasons.append("shared_play_group:" + ",".join(shared_groups))

    shared_atoms = sorted(set(source.get("technique_atoms") or []) & set(target.get("technique_atoms") or []))
    if shared_atoms:
        atom_score = min(20, 10 * len(shared_atoms))
        score += atom_score
        reasons.append("shared_technique_atoms:" + ",".join(shared_atoms))

    if source.get("content_type") and source.get("content_type") == target.get("content_type"):
        score += 5
        reasons.append("same_content_type")

    if target.get("status") == "published" and target.get("published_url"):
        score += 5
        reasons.append("target_already_published")

    return score, reasons


def plan_internal_links(article_id: str, limit: int = 3, min_score: int = DEFAULT_MIN_SCORE) -> dict:
    rows = _linkable_records()
    source = next((row for row in rows if row.get("article_id") == article_id), None)
    if source is None:
        return {
            "article_id": article_id,
            "status": "source_not_linkable",
            "targets": [],
        }

    candidates = []
    for target in rows:
        target_id = str(target.get("article_id") or "")
        if not target_id or target_id == article_id:
            continue
        score, reasons = _score(source, target)
        if score < min_score:
            continue
        published_url = str(target.get("published_url") or "").strip()
        candidates.append({
            "target_article_id": target_id,
            "anchor_hint": canonical_primary_keyword(target),
            "score": score,
            "reasons": reasons,
            "resolution_status": "resolved" if published_url else "pending_published_url",
            "url": published_url or None,
        })

    candidates.sort(key=lambda item: (-item["score"], item["target_article_id"]))
    return {
        "article_id": article_id,
        "status": "planned",
        "min_score": min_score,
        "limit": limit,
        "targets": candidates[: max(0, limit)],
    }


def plan_all_internal_links(limit: int = 3, min_score: int = DEFAULT_MIN_SCORE) -> dict:
    rows = _linkable_records()
    plans = [plan_internal_links(str(row["article_id"]), limit=limit, min_score=min_score) for row in rows]
    return {
        "article_count": len(rows),
        "limit": limit,
        "min_score": min_score,
        "resolved_targets": sum(
            1 for plan in plans for target in plan["targets"] if target["resolution_status"] == "resolved"
        ),
        "pending_targets": sum(
            1 for plan in plans for target in plan["targets"] if target["resolution_status"] == "pending_published_url"
        ),
        "plans": plans,
    }


def audit_internal_link_plan(plan: dict) -> list[str]:
    errors: list[str] = []
    source_id = str(plan.get("article_id") or "")
    seen: set[str] = set()
    for target in plan.get("targets") or []:
        target_id = str(target.get("target_article_id") or "")
        if not target_id:
            errors.append("missing target_article_id")
            continue
        if target_id == source_id:
            errors.append("self link is prohibited")
        if target_id in seen:
            errors.append("duplicate target_article_id: " + target_id)
        seen.add(target_id)
        resolution = target.get("resolution_status")
        url = target.get("url")
        if resolution == "resolved" and not url:
            errors.append("resolved target missing url: " + target_id)
        if resolution == "pending_published_url" and url:
            errors.append("pending target must not carry url: " + target_id)
        if int(target.get("score") or 0) < int(plan.get("min_score") or DEFAULT_MIN_SCORE):
            errors.append("target below semantic threshold: " + target_id)
    return errors
