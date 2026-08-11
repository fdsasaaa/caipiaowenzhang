from __future__ import annotations

from .ai_generation import GenerationError, generate_article
from .approval import evaluate_and_record, evaluate_for_approval
from .draft_packets import build_draft_packet
from .semantic_dedup import structural_similarity
from .seo_priority import rank_generated_topics


def select_nonoverlapping_topics(ranked: list[dict], count: int, threshold: float = 0.82) -> tuple[list[dict], list[dict]]:
    selected: list[dict] = []
    skipped: list[dict] = []
    for row in ranked:
        if not row.get("eligible"):
            skipped.append({"article_id": row.get("article_id"), "reason": "ranking_ineligible"})
            continue
        blueprint = row.get("blueprint") or {}
        overlap = None
        for chosen in selected:
            score, reasons = structural_similarity(blueprint, chosen.get("blueprint") or {})
            if score >= threshold:
                overlap = {
                    "article_id": row.get("article_id"),
                    "reason": "same_batch_structural_overlap",
                    "overlap_with": chosen.get("article_id"),
                    "score": round(score, 4),
                    "reasons": reasons,
                }
                break
        if overlap:
            skipped.append(overlap)
            continue
        selected.append(row)
        if len(selected) >= count:
            break
    return selected, skipped


def produce_ranked_batch(
    provider_id: str,
    lottery: str,
    play: str,
    *,
    count: int = 5,
    signals: list[dict] | None = None,
    model: str | None = None,
    api_key: str | None = None,
    transport=None,
    record: bool = False,
) -> dict:
    ranking = rank_generated_topics(provider_id, lottery, play, max(count * 4, count), signals)
    selected, skipped = select_nonoverlapping_topics(ranking.get("ranked", []), count)
    results = []
    for row in selected:
        blueprint = row["blueprint"]
        packet = build_draft_packet(blueprint)
        item = {
            "article_id": blueprint.get("article_id"),
            "priority_score": row.get("priority_score"),
            "priority_band": row.get("priority_band"),
            "signal_mode": row.get("signal_mode"),
            "blueprint": blueprint,
            "packet": packet,
        }
        try:
            generation = generate_article(
                packet,
                model=model,
                api_key=api_key,
                transport=transport,
            )
        except GenerationError as exc:
            item.update({"status": "generation_failed", "error": str(exc), "approved": False})
            results.append(item)
            continue
        article = generation.article
        approval = evaluate_and_record(packet, article) if record else evaluate_for_approval(packet, article)
        item.update({
            "status": approval.status,
            "approved": approval.approved,
            "model_provider": generation.provider,
            "model": generation.model,
            "response_id": generation.response_id,
            "draft": article,
            "approval": {
                "quality_score": approval.quality_score,
                "errors": approval.errors,
                "warnings": approval.warnings,
                "registry_record": approval.registry_record,
            },
            "approved_package": approval.publish_package,
        })
        results.append(item)
    return {
        "provider_id": provider_id,
        "lottery": lottery,
        "play": play,
        "requested": count,
        "selected": len(selected),
        "generated": sum(item.get("status") != "generation_failed" for item in results),
        "approved": sum(bool(item.get("approved")) for item in results),
        "failed": sum(not bool(item.get("approved")) for item in results),
        "signal_mode": ranking.get("signal_mode"),
        "same_batch_skipped": skipped,
        "results": results,
    }
