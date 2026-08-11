from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .article_memory import append_article_state, get_article_record
from .claim_evidence import audit_claim_evidence
from .draft_packets import review_draft
from .quality import evaluate as evaluate_quality
from .seo_keywords import keyword_owners
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


def _existing_identity(article_id: str | None) -> dict:
    if not article_id:
        return {}
    return get_article_record(article_id) or {}


def _enrich_for_quality(packet: dict, article: dict) -> dict:
    facts = packet.get("immutable_facts", {})
    existing = _existing_identity(article.get("article_id") or packet.get("article_id"))
    enriched = dict(article)
    values = {
        "provider_id": facts.get("provider_id") or existing.get("provider_id"),
        "lottery": facts.get("lottery") or existing.get("lottery"),
        "play": facts.get("play") or existing.get("play"),
        "subject_lottery": facts.get("subject_lottery") or existing.get("subject_lottery") or facts.get("lottery") or existing.get("lottery"),
        "subject_play": facts.get("subject_play") or existing.get("subject_play") or facts.get("play") or existing.get("play"),
        "content_type": facts.get("content_type") or existing.get("content_type"),
        "site_category_key": facts.get("site_category_key") or existing.get("site_category_key"),
        "content_format": facts.get("content_format") or existing.get("content_format"),
        "technique_atoms": facts.get("technique_atoms") or existing.get("technique_atoms", []),
        "case_scope": facts.get("case_scope") or existing.get("case_scope"),
        "rule_refs": facts.get("rule_refs") or existing.get("rule_refs", []),
        "source_refs": facts.get("source_refs") or existing.get("source_refs", []),
        "fingerprint": facts.get("fingerprint") or existing.get("fingerprint"),
        "case_structure": facts.get("case_structure") or existing.get("case_structure", ""),
        "information_gain_type": facts.get("information_gain_type") or existing.get("information_gain_type", "method_mechanics_and_reproducible_case"),
    }
    for field, value in values.items():
        enriched.setdefault(field, value)
    return enriched


def _seo_contract(packet: dict, article: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seo = packet.get("seo", {})
    primary_keyword = str(article.get("primary_keyword") or "").strip()
    if primary_keyword != seo.get("primary_keyword"):
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
    if primary_keyword:
        owners = keyword_owners(primary_keyword, exclude_article_id=article.get("article_id") or packet.get("article_id"))
        if owners:
            errors.append(
                "exact primary_keyword already owned by active article: "
                + str(owners[0].get("article_id") or "unknown")
            )
    return errors, warnings


def _semantic_category(content_type: str | None) -> str:
    return {
        "technique_article": "投注技巧",
        "hangup_scheme": "挂机方案",
        "resource_article": "资源应用",
        "seo_topic": "SEO文章",
    }.get(content_type or "", content_type or "彩票技巧")


def _publish_package(packet: dict, article: dict) -> dict:
    facts = packet["immutable_facts"]
    seo = packet["seo"]
    existing = _existing_identity(article.get("article_id"))
    secondary = article.get("secondary_keywords") or seo.get("secondary_keywords", [])
    content_type = facts.get("content_type") or existing.get("content_type")
    category = article.get("category") or _semantic_category(content_type)
    subject_play = facts.get("subject_play") or existing.get("subject_play") or facts.get("play") or existing.get("play")
    tags = article.get("tags") or list(dict.fromkeys([subject_play, *secondary]))
    tags = [x for x in tags if x]
    package = {
        "article_id": article["article_id"],
        "title": article["title"],
        "seo_title": article.get("seo_title") or article["title"],
        "slug": article["slug"],
        "meta_description": article["meta_description"],
        "primary_keyword": article["primary_keyword"],
        "secondary_keywords": secondary,
        "search_intent": article["search_intent"],
        "summary": article.get("summary", ""),
        "category": category,
        "site_category_key": facts.get("site_category_key") or existing.get("site_category_key"),
        "content_type": content_type,
        "content_format": facts.get("content_format") or existing.get("content_format"),
        "tags": tags,
        "content": article["content"],
        "internal_links": article.get("internal_links", []),
        "rule_refs": facts.get("rule_refs") or existing.get("rule_refs", []),
        "source_refs": facts.get("source_refs") or existing.get("source_refs", []),
        "case_scope": facts.get("case_scope") or existing.get("case_scope", "mechanics_only"),
        "provider_id": facts.get("provider_id") or existing.get("provider_id"),
        "lottery": facts.get("lottery") or existing.get("lottery"),
        "play": facts.get("play") or existing.get("play"),
        "subject_lottery": facts.get("subject_lottery") or existing.get("subject_lottery") or facts.get("lottery") or existing.get("lottery"),
        "subject_play": subject_play,
        "technique_atoms": facts.get("technique_atoms") or existing.get("technique_atoms", []),
        "fingerprint": facts.get("fingerprint") or existing.get("fingerprint"),
        "content_hash": sha256_text(article["content"]),
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "status": "approved",
    }
    if article.get("generation_contract_version"):
        package["generation_contract_version"] = article["generation_contract_version"]
        package["claim_evidence"] = article.get("claim_evidence", [])
    for field in ("revision_reason", "revision_of_content_hash"):
        if article.get(field):
            package[field] = article[field]
    return package


def _registry_changes(packet: dict, article: dict) -> dict:
    facts = packet.get("immutable_facts", {})
    changes = {
        "blueprint_id": packet.get("blueprint_id"),
        "provider_id": facts.get("provider_id"),
        "title": article.get("title") or packet.get("seo", {}).get("title"),
        "slug": article.get("slug") or packet.get("seo", {}).get("slug_seed"),
        "primary_keyword": article.get("primary_keyword") or packet.get("seo", {}).get("primary_keyword"),
        "secondary_keywords": article.get("secondary_keywords") or packet.get("seo", {}).get("secondary_keywords", []),
        "search_intent": article.get("search_intent") or packet.get("seo", {}).get("search_intent"),
        "lottery": facts.get("lottery"),
        "play": facts.get("play"),
        "subject_lottery": facts.get("subject_lottery") or facts.get("lottery"),
        "subject_play": facts.get("subject_play") or facts.get("play"),
        "content_type": facts.get("content_type"),
        "site_category_key": facts.get("site_category_key"),
        "content_format": facts.get("content_format"),
        "technique_family": facts.get("technique_family"),
        "technique_atoms": facts.get("technique_atoms", []),
        "case_scope": facts.get("case_scope"),
        "rule_refs": facts.get("rule_refs", []),
        "source_refs": facts.get("source_refs", []),
        "case_structure": facts.get("case_structure"),
        "information_gain_type": facts.get("information_gain_type"),
        "content_hash": sha256_text(article.get("content", "")) if article.get("content") else None,
    }
    if article.get("generation_contract_version"):
        changes["generation_contract_version"] = article.get("generation_contract_version")
        changes["claim_evidence"] = article.get("claim_evidence", [])
    for field in ("revision_reason", "revision_of_content_hash"):
        if article.get(field):
            changes[field] = article[field]
    return changes


def evaluate_for_approval(packet: dict, article: dict) -> ApprovalResult:
    draft_review = review_draft(packet, article)
    evidence_report = audit_claim_evidence(packet, article)
    enriched = _enrich_for_quality(packet, article)
    quality_report = evaluate_quality(enriched)
    seo_errors, seo_warnings = _seo_contract(packet, article)

    errors = list(dict.fromkeys([*draft_review.errors, *evidence_report.errors, *quality_report.errors, *seo_errors]))
    warnings = list(dict.fromkeys([*draft_review.warnings, *evidence_report.warnings, *quality_report.warnings, *seo_warnings]))
    approved = not errors and draft_review.passed and evidence_report.passed and quality_report.passed
    status = "approved" if approved else "rejected_for_revision"
    package = _publish_package(packet, enriched) if approved else None
    existing = _existing_identity(enriched.get("article_id"))
    preview_registry = dict(existing)
    preview_registry.update(_registry_changes(packet, enriched))
    preview_registry["article_id"] = enriched.get("article_id")
    preview_registry["status"] = status
    return ApprovalResult(
        approved=approved,
        status=status,
        errors=errors,
        warnings=warnings,
        quality_score=quality_report.score,
        publish_package=package,
        registry_record=preview_registry,
    )


def evaluate_and_record(packet: dict, article: dict) -> ApprovalResult:
    result = evaluate_for_approval(packet, article)
    article_id = article.get("article_id") or packet.get("article_id")
    if article_id:
        result.registry_record = append_article_state(article_id, result.status, _registry_changes(packet, article))
    return result
