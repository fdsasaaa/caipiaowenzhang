from __future__ import annotations

from html import escape

from .internal_links import audit_internal_link_plan
from .site_urls import ALLOWED_SITE_HOSTS, validate_published_url
from .text import sha256_text

RELATED_MARKER = 'data-lcm-related-reading="1"'


def _revision_article_from_package(package: dict, content: str, links: list[dict]) -> dict:
    fields = [
        "article_id",
        "title",
        "seo_title",
        "slug",
        "meta_description",
        "primary_keyword",
        "secondary_keywords",
        "search_intent",
        "summary",
        "category",
        "site_category_key",
        "content_type",
        "content_format",
        "tags",
        "rule_refs",
        "source_refs",
        "case_scope",
        "provider_id",
        "lottery",
        "play",
        "subject_lottery",
        "subject_play",
        "technique_atoms",
        "fingerprint",
    ]
    article = {field: package.get(field) for field in fields if field in package}
    article["content"] = content
    article["internal_links"] = links
    article["status"] = "draft"
    article["revision_reason"] = "internal_links"
    article["revision_of_content_hash"] = package.get("content_hash")
    article["proposed_content_hash"] = sha256_text(content)
    return article


def build_internal_link_revision(
    package: dict,
    plan: dict,
    max_links: int = 3,
    allowed_hosts: set[str] | None = None,
) -> dict:
    """Create a draft revision; never return an approved package.

    Only resolved, validated internal URLs are rendered. The revised HTML must be
    sent back through the normal Draft Review + Approval Pipeline because its
    content hash differs from the previously approved content.
    """
    allowed_hosts = set(allowed_hosts or ALLOWED_SITE_HOSTS)
    if package.get("status") != "approved":
        raise ValueError("internal link revision requires an approved package")
    article_id = str(package.get("article_id") or "")
    if not article_id:
        raise ValueError("approved package missing article_id")
    if plan.get("article_id") != article_id:
        raise ValueError("internal link plan article_id does not match package")
    if str(package.get("content_format") or "").lower() != "html":
        raise ValueError("internal link revision currently requires html content")

    original_content = str(package.get("content") or "")
    original_hash = str(package.get("content_hash") or "")
    if not original_content or not original_hash:
        raise ValueError("approved package missing content/content_hash")
    if sha256_text(original_content) != original_hash:
        raise ValueError("approved package content_hash does not match content bytes")
    if RELATED_MARKER in original_content:
        raise ValueError("approved content already contains managed related-reading block")

    plan_errors = audit_internal_link_plan(plan)
    if plan_errors:
        raise ValueError("invalid internal link plan: " + "; ".join(plan_errors))

    resolved = [target for target in (plan.get("targets") or []) if target.get("resolution_status") == "resolved"]
    if not resolved:
        raise ValueError("internal link revision requires at least one resolved target URL")

    rendered_links: list[dict] = []
    seen_targets: set[str] = set()
    seen_urls: set[str] = set()
    for target in resolved:
        if len(rendered_links) >= max(0, max_links):
            break
        target_id = str(target.get("target_article_id") or "").strip()
        anchor = str(target.get("anchor_hint") or "").strip()
        url = str(target.get("url") or "").strip()
        if not target_id or target_id == article_id:
            raise ValueError("invalid or self target_article_id")
        if not anchor:
            raise ValueError("resolved internal link missing anchor_hint")
        if len(anchor) > 100:
            raise ValueError("internal link anchor_hint is too long")
        url = validate_published_url(url, allowed_hosts)
        if target_id in seen_targets or url in seen_urls:
            raise ValueError("duplicate internal link target/url")
        seen_targets.add(target_id)
        seen_urls.add(url)
        rendered_links.append({
            "target_article_id": target_id,
            "anchor": anchor,
            "url": url,
        })

    if not rendered_links:
        raise ValueError("no resolved internal links survived revision gate")

    items = "".join(
        '<li><a href="' + escape(link["url"], quote=True) + '" data-target-article-id="'
        + escape(link["target_article_id"], quote=True) + '">' + escape(link["anchor"]) + "</a></li>"
        for link in rendered_links
    )
    related = (
        '<section class="related-reading" data-lcm-related-reading="1">'
        '<h2>相关阅读</h2><ul>' + items + "</ul></section>"
    )
    revised_content = original_content.rstrip() + "\n" + related
    if sha256_text(revised_content) == original_hash:
        raise ValueError("internal link revision did not change content hash")

    return _revision_article_from_package(package, revised_content, rendered_links)
