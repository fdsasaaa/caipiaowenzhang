from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .article_angle_quality import evaluate_article_angle
from .article_memory import append_article_state, get_article_record
from .claim_evidence import audit_claim_evidence
from .draft_packets import review_draft
from .editorial_quality import evaluate_editorial
from .quality import evaluate as evaluate_quality
from .seo_keywords import keyword_owners
from .site_contract import normalize_seo_cluster_assignment, seo_cluster_article_category_key
from .text import sha256_text
from .title_seo_runtime import apply_title_seo


@dataclass
class ApprovalResult:
    approved: bool
    status: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    quality_score: int = 0
    editorial_score: int = 100
    angle_score: int | None = None
    publish_package: dict | None = None
    registry_record: dict | None = None


def _existing_identity(article_id: str | None) -> dict:
    if not article_id:
        return {}
    return get_article_record(article_id) or {}


def _cluster_assignment(packet: dict, existing: dict) -> tuple[str | None, list[str]]:
    facts = packet.get("immutable_facts", {})
    primary = facts["primary_seo_cluster_id"] if "primary_seo_cluster_id" in facts else existing.get("primary_seo_cluster_id")
    secondary = facts["secondary_seo_cluster_ids"] if "secondary_seo_cluster_ids" in facts else existing.get("secondary_seo_cluster_ids", [])
    return normalize_seo_cluster_assignment(primary, secondary)


def _enrich_for_quality(packet: dict, article: dict) -> dict:
    facts = packet.get("immutable_facts", {})
    existing = _existing_identity(article.get("article_id") or packet.get("article_id"))
    enriched = dict(article)
    values = {
        "provider_id": facts.get("provider_id") or existing.get("provider_id"),
        "provider_response_id": article.get("provider_response_id") or existing.get("provider_response_id"),
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
        "angle_signature": facts.get("angle_signature") or existing.get("angle_signature"),
        "article_angle_contract_version": facts.get("article_angle_contract_version") or existing.get("article_angle_contract_version"),
        "angle_contract_verified": bool(facts.get("angle_contract_verified") or existing.get("angle_contract_verified")),
        "primary_seo_cluster_id": facts.get("primary_seo_cluster_id") if "primary_seo_cluster_id" in facts else existing.get("primary_seo_cluster_id"),
        "secondary_seo_cluster_ids": facts.get("secondary_seo_cluster_ids") if "secondary_seo_cluster_ids" in facts else existing.get("secondary_seo_cluster_ids", []),
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
    # Primary Keyword remains an ownership field. Title SEO V1.0 deliberately does
    # not require exact-keyword inclusion or a 分分时时彩 prefix in the human title.
    if primary_keyword:
        owners = keyword_owners(primary_keyword, exclude_article_id=article.get("article_id") or packet.get("article_id"))
        if owners:
            errors.append(
                "exact primary_keyword already owned by active article: "
                + str(owners[0].get("article_id") or "unknown")
            )

    existing = _existing_identity(article.get("article_id") or packet.get("article_id"))
    try:
        primary_cluster, _secondary_clusters = _cluster_assignment(packet, existing)
        if primary_cluster:
            facts = packet.get("immutable_facts", {})
            site_category_key = facts.get("site_category_key") or existing.get("site_category_key")
            if site_category_key != seo_cluster_article_category_key():
                errors.append("SEO cluster assignment is only valid for the configured ordinary article carrier")
    except ValueError as exc:
        errors.append(str(exc))
    return errors, warnings


def _semantic_category(content_type: str | None) -> str:
    return {
        "technique_article": "投注技巧",
        "hangup_scheme": "挂机方案",
        "resource_article": "资源应用",
        "seo_topic": "投注机巧",
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
    primary_cluster, secondary_clusters = _cluster_assignment(packet, existing)
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
    for field in ("title_seo_contract_version", "title_candidates", "title_selection_reason", "title_review"):
        if article.get(field) is not None:
            package[field] = article[field]
    provider_response_id = article.get("provider_response_id") or existing.get("provider_response_id")
    if provider_response_id:
        package["provider_response_id"] = provider_response_id
    angle_contract = packet.get("article_angle_contract") or {}
    if packet.get("article_angle_contract_version") and article.get("angle_approval_passed") is True:
        package["article_angle_contract_version"] = packet["article_angle_contract_version"]
        package["information_gain_type"] = angle_contract.get("angle_type")
        package["angle_signature"] = facts.get("angle_signature") or existing.get("angle_signature")
        package["angle_contract_verified"] = True
        package["angle_approval_passed"] = True
        package["article_angle_contract"] = angle_contract
        package["angle_delivery"] = article.get("angle_delivery") or {}
    if primary_cluster:
        package["primary_seo_cluster_id"] = primary_cluster
        package["secondary_seo_cluster_ids"] = secondary_clusters
    if article.get("generation_contract_version"):
        package["generation_contract_version"] = article["generation_contract_version"]
        package["claim_evidence"] = article.get("claim_evidence", [])
    if article.get("editorial_contract_version"):
        package["editorial_contract_version"] = article["editorial_contract_version"]
        package["practical_guidance"] = article.get("practical_guidance", {})
    for field in ("revision_reason", "revision_of_content_hash"):
        if article.get(field):
            package[field] = article[field]
    return package


def _registry_changes(packet: dict, article: dict) -> dict:
    facts = packet.get("immutable_facts", {})
    existing = _existing_identity(article.get("article_id") or packet.get("article_id"))
    try:
        primary_cluster, secondary_clusters = _cluster_assignment(packet, existing)
    except ValueError:
        primary_cluster, secondary_clusters = None, []
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
        "angle_signature": facts.get("angle_signature") or existing.get("angle_signature"),
        "content_hash": sha256_text(article.get("content", "")) if article.get("content") else None,
        "provider_response_id": article.get("provider_response_id") or existing.get("provider_response_id"),
    }
    for field in ("title_seo_contract_version", "title_candidates", "title_selection_reason", "title_review"):
        if article.get(field) is not None:
            changes[field] = article[field]
    angle_contract = packet.get("article_angle_contract") or {}
    if packet.get("article_angle_contract_version"):
        changes["article_angle_contract_version"] = packet["article_angle_contract_version"]
        changes["information_gain_type"] = angle_contract.get("angle_type")
        changes["angle_contract_verified"] = True
        changes["angle_approval_passed"] = bool(article.get("angle_approval_passed"))
        changes["angle_delivery"] = article.get("angle_delivery") or {}
    if primary_cluster:
        changes["primary_seo_cluster_id"] = primary_cluster
        changes["secondary_seo_cluster_ids"] = secondary_clusters
    if article.get("generation_contract_version"):
        changes["generation_contract_version"] = article.get("generation_contract_version")
        changes["claim_evidence"] = article.get("claim_evidence", [])
    if article.get("editorial_contract_version"):
        changes["editorial_contract_version"] = article.get("editorial_contract_version")
        changes["practical_guidance"] = article.get("practical_guidance", {})
    for field in ("revision_reason", "revision_of_content_hash"):
        if article.get(field):
            changes[field] = article[field]
    return changes


def evaluate_for_approval(packet: dict, article: dict) -> ApprovalResult:
    # Approval owns the final fail-closed decision even if an upstream generation
    # path did not run normalization. This call is idempotent when candidates and
    # a selected title already exist.
    title_report = apply_title_seo(article, packet=packet)
    draft_review = review_draft(packet, article)
    evidence_report = audit_claim_evidence(packet, article)
    enriched = _enrich_for_quality(packet, article)
    enriched["title_review"] = title_report.as_dict()
    quality_report = evaluate_quality(enriched)
    editorial_report = evaluate_editorial(packet, article)
    angle_report = evaluate_article_angle(packet, article)
    if angle_report.contracted:
        enriched["article_angle_contract_version"] = packet.get("article_angle_contract_version")
        enriched["information_gain_type"] = (packet.get("article_angle_contract") or {}).get("angle_type")
        enriched["angle_contract_verified"] = True
        enriched["angle_approval_passed"] = angle_report.passed
        enriched["angle_delivery"] = article.get("angle_delivery") or {}
    seo_errors, seo_warnings = _seo_contract(packet, article)

    errors = list(dict.fromkeys([
        *draft_review.errors, *evidence_report.errors, *quality_report.errors,
        *editorial_report.errors, *angle_report.errors, *title_report.errors, *seo_errors,
    ]))
    warnings = list(dict.fromkeys([
        *draft_review.warnings, *evidence_report.warnings, *quality_report.warnings,
        *editorial_report.warnings, *angle_report.warnings, *seo_warnings,
    ]))
    approved = (
        not errors
        and draft_review.passed
        and evidence_report.passed
        and quality_report.passed
        and editorial_report.passed
        and angle_report.passed
        and title_report.passed
    )
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
        editorial_score=editorial_report.score,
        angle_score=angle_report.score if angle_report.contracted else None,
        publish_package=package,
        registry_record=preview_registry,
    )


def evaluate_and_record(packet: dict, article: dict) -> ApprovalResult:
    result = evaluate_for_approval(packet, article)
    article_id = article.get("article_id") or packet.get("article_id")
    if article_id:
        record_article = _enrich_for_quality(packet, article)
        if result.registry_record:
            for field in (
                "article_angle_contract_version", "information_gain_type", "angle_signature",
                "angle_contract_verified", "angle_approval_passed", "angle_delivery",
                "title_seo_contract_version", "title_candidates", "title_selection_reason", "title_review",
            ):
                if field in result.registry_record:
                    record_article[field] = result.registry_record[field]
        result.registry_record = append_article_state(article_id, result.status, _registry_changes(packet, record_article))
    return result
