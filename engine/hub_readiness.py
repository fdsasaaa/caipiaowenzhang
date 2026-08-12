from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .site_contract import allowed_seo_cluster_ids, normalize_seo_cluster_assignment
from .store import ROOT, iter_registry


def _load_package(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid approved package {path.name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"approved package must be a JSON object: {path.name}")
    return payload


def audit_hub_readiness(
    approved_dir: Path | None = None,
    registry_rows: Iterable[dict] | None = None,
    allowed_clusters: Iterable[str] | None = None,
) -> dict:
    """Inventory formal Approved Packages by explicit SEO cluster metadata.

    This is deliberately an evidence inventory, not an automatic Hub creator.
    Registry-approved lifecycle records are reported separately because a
    registry status does not mean a transportable Approved Package exists in
    articles/approved/.
    """
    approved_dir = approved_dir or (ROOT / "articles" / "approved")
    clusters = tuple(allowed_clusters or allowed_seo_cluster_ids())
    cluster_set = set(clusters)
    cluster_rows = {
        cluster_id: {
            "cluster_id": cluster_id,
            "primary_package_count": 0,
            "membership_package_count": 0,
            "package_ids": [],
            "coverage_status": "no_formal_package_coverage",
        }
        for cluster_id in clusters
    }

    errors: list[str] = []
    package_count = 0
    assigned_count = 0
    unassigned_count = 0
    seen_article_ids: set[str] = set()

    for path in sorted(approved_dir.glob("*.json")) if approved_dir.exists() else []:
        package_count += 1
        try:
            package = _load_package(path)
            article_id = str(package.get("article_id") or "").strip()
            if not article_id:
                raise ValueError(f"approved package missing article_id: {path.name}")
            if article_id in seen_article_ids:
                raise ValueError(f"duplicate article_id in approved inventory: {article_id}")
            seen_article_ids.add(article_id)
            if package.get("status") != "approved":
                raise ValueError(f"formal approved package status must be approved: {path.name}")
            if str(package.get("site_category_key") or "").strip() != "tzjq":
                raise ValueError(f"Hub readiness only accepts tzjq article packages: {path.name}")

            primary, secondary = normalize_seo_cluster_assignment(
                package.get("primary_seo_cluster_id"),
                package.get("secondary_seo_cluster_ids"),
            )
            if primary is None:
                unassigned_count += 1
                continue

            assigned_count += 1
            memberships = [primary, *secondary]
            for cluster_id in memberships:
                if cluster_id not in cluster_set:
                    raise ValueError(f"unknown SEO cluster id in approved package: {cluster_id}")
                cluster_rows[cluster_id]["membership_package_count"] += 1
                cluster_rows[cluster_id]["package_ids"].append(article_id)
            cluster_rows[primary]["primary_package_count"] += 1
        except ValueError as exc:
            errors.append(str(exc))

    for row in cluster_rows.values():
        if row["membership_package_count"] > 0:
            row["coverage_status"] = "formal_package_coverage_present_editorial_review_required"

    effective_registry = list(registry_rows) if registry_rows is not None else list(iter_registry("articles"))
    registry_approved_count = sum(1 for row in effective_registry if row.get("status") == "approved")
    registry_cluster_assigned_count = sum(
        1
        for row in effective_registry
        if row.get("status") == "approved" and str(row.get("primary_seo_cluster_id") or "").strip()
    )

    return {
        "ok": not errors,
        "formal_approved_package_count": package_count,
        "formal_cluster_assigned_package_count": assigned_count,
        "formal_cluster_unassigned_package_count": unassigned_count,
        "registry_approved_article_count": registry_approved_count,
        "registry_cluster_assigned_approved_count": registry_cluster_assigned_count,
        "transport_inventory_present": package_count > 0,
        "transport_inventory_valid": package_count > 0 and not errors,
        "automatic_hub_creation_allowed": False,
        "automatic_hub_ready_decision_allowed": False,
        "readiness_rule": "coverage evidence only; substantive Hub readiness requires editorial/SEO review plus distinct intent, useful Hub copy, real internal links, HTTP 200 and self-canonical verification",
        "clusters": [cluster_rows[cluster_id] for cluster_id in clusters],
        "errors": errors,
    }
