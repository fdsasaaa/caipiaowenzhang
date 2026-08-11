from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .draft_packets import review_draft
from .quality import evaluate as evaluate_quality
from .text import sha256_text


@dataclass
class ApprovalResult:
    approved: bool
    status: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    quality_score: int = 0
    publish_package: dict | None = None
    registry_record: dict | None = None


def _enrich_for_quality(packet: dict, article: dict) -> dict:
    facts = packet.get("immutable_facts", {})
    enriched = dict(article)
    enriched.setdefault("provider_id", facts.get("provider_id"))
    enriched.setdefault("lottery", facts.get("lottery"))
    enriched.setdefault("play", facts.get("play"))
    enriched.setdefault("technique_atoms", facts.get("technique_atoms", []))
    enriched.setdefault("case_scope", facts.get("case_scope"))
    enriched.setdefault("rule_refs", facts.get("rule_refs", []))
    enriched.setdefault("source_refs", facts.get("source_refs", []))
    enriched.setdefault("fingerprint", facts.get("fingerprint"))
    enriched.setdefault("case_structure", facts.get("case_structure", ""))
    enriched.setdefault("information_gain_type", facts.get("information_gain_type", "method_mechanics_and_reproducible_case"))
    return enriched


def _seo_contract(packet: dict, article: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seo = packet.get("seo", {})
    if article.get("primary_keyword") != seo.get("primary_keyword"):
        errors.append("primary_keyword differs from draft packet")
    if article.get("search_intent") != seo.get("search_intent"):
        errors.append("search_intent differs from draft packet")
    if not article.get("meta_description"):
        errors.append("meta_description missing")
    if not article.get("slug"):
        errors.append("slug missing")
    title = article.get("title", "") or ""
    if not title:
        errors.append("title missing")
    elif seo.get("primary_keyword") and seo["primary_keyword"] not in title:
        warnings.append("title does not contain exact primary keyword; verify natural SEO wording")
    return errors, warnings


def _publish_package(packet: dict, article: dict) -> dict:
    facts = packet["immutable_facts"]
    seo = packet["seo"]
    secondary = article.get("secondary_keywords") or seo.get("secondary_keywords", [])
    category = article.get("category") or facts.get("lottery") or "彩票技巧"
    tags = article.get("tags") or list(dict.fromkeys([facts.get("play"), *secondary]))
    tags = [x for x in tags if x]
    return {
        "article_id": article["article_id"],
        "title": article["title"],
        "slug": article["slug"],
        "meta_description": article["meta_description"],
        "primary_keyword": article["primary_keyword"],
        "secondary_keywords": secondary,
        "search_intent": article["search_intent"],
        "category": category,
        "tags": tags,
        "content": article["content"],
        "internal_links": article.get("internal_links", []),
        "rule_refs": facts.get("rule_refs", []),
        "source_refs": facts.get("source_refs", []),
        "case_scope": facts.get("case_scope", "mechanics_only"),
        "provider_id": facts.get("provider_id"),
        "lottery": facts.get("lottery"),
        "play": facts.get("play"),
        "technique_atoms": facts.get("technique_atoms", []),
        "fingerprint": facts.get("fingerprint"),
        "content_hash": sha256_text(article["content"]),
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "status": "approved",
    }


def _registry_record(packet: dict, article: dict, status: str) -> dict:
    facts = packet.get("immutable_facts", {})
    return {
        "article_id": article.get("article_id") or packet.get("article_id"),
        "blueprint_id": packet.get("blueprint_id"),
        "provider_id": facts.get("provider_id"),
        "title": article.get("title") or packet.get("seo", {}).get("title"),
        "slug": article.get("slug") or packet.get("seo", {}).get("slug_seed"),
        "primary_keyword": article.get("primary_keyword") or packet.get("seo", {}).get("primary_keyword"),
        "secondary_keywords": article.get("secondary_keywords") or packet.get("seo", {}).get("secondary_keywords", []),
        "search_intent": article.get("search_intent") or packet.get("seo", {}).get("search_intent"),
        "information_gain_type": facts.get("information_gain_type", "method_mechanics_and_reproducible_case"),
        "lottery": facts.get("lottery"),
        "play": facts.get("play"),
        "technique_family": facts.get("technique_family"),
        "technique_atoms": facts.get("technique_atoms", []),
        "case_structure": facts.get("case_structure", ""),
        "case_scope": facts.get("case_scope"),
        "rule_refs": facts.get("rule_refs", []),
        "source_refs": facts.get("source_refs", []),
        "fingerprint": facts.get("fingerprint"),
        "content_hash": sha256_text(article.get("content", "")) if article.get("content") else None,
        "status": status,
        "published_url": article.get("published_url"),
        "published_at": article.get("published_at"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def evaluate_for_approval(packet: dict, article: dict) -> ApprovalResult:
    draft_review = review_draft(packet, article)
    enriched = _enrich_for_quality(packet, article)
    quality_report = evaluate_quality(enriched)
    seo_errors, seo_warnings = _seo_contract(packet, article)

    errors = [*draft_review.errors, *quality_report.errors, *seo_errors]
    warnings = [*draft_review.warnings, *quality_report.warnings, *seo_warnings]
    # Keep deterministic order while removing duplicate strings.
    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))
    approved = not errors and draft_review.passed and quality_report.passed
    status = "approved" if approved else "rejected_for_revision"
    package = _publish_package(packet, enriched) if approved else None
    registry = _registry_record(packet, enriched, status)
    return ApprovalResult(
        approved=approved,
        status=status,
        errors=errors,
        warnings=warnings,
        quality_score=quality_report.score,
        publish_package=package,
        registry_record=registry,
    )
