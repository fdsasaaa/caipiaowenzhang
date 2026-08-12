from __future__ import annotations

import json

from engine.hub_readiness import audit_hub_readiness


ALLOWED = ("ffc_research", "research_lab")


def _write(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_registry_approved_is_not_formal_transport_inventory(tmp_path):
    approved = tmp_path / "approved"
    approved.mkdir()
    report = audit_hub_readiness(
        approved_dir=approved,
        registry_rows=[{"article_id": "A1", "status": "approved"}],
        allowed_clusters=ALLOWED,
    )
    assert report["ok"] is True
    assert report["formal_approved_package_count"] == 0
    assert report["registry_approved_article_count"] == 1
    assert report["transport_inventory_present"] is False
    assert report["automatic_hub_creation_allowed"] is False


def test_explicit_cluster_package_counts_as_coverage_not_auto_ready(tmp_path, monkeypatch):
    approved = tmp_path / "approved"
    approved.mkdir()
    _write(
        approved / "a1.json",
        {
            "article_id": "A1",
            "status": "approved",
            "site_category_key": "tzjq",
            "primary_seo_cluster_id": "ffc_research",
            "secondary_seo_cluster_ids": ["research_lab"],
        },
    )
    monkeypatch.setattr("engine.hub_readiness.normalize_seo_cluster_assignment", lambda primary, secondary: (primary, secondary))
    report = audit_hub_readiness(
        approved_dir=approved,
        registry_rows=[],
        allowed_clusters=ALLOWED,
    )
    assert report["ok"] is True
    assert report["formal_approved_package_count"] == 1
    assert report["formal_cluster_assigned_package_count"] == 1
    by_id = {row["cluster_id"]: row for row in report["clusters"]}
    assert by_id["ffc_research"]["primary_package_count"] == 1
    assert by_id["ffc_research"]["membership_package_count"] == 1
    assert by_id["research_lab"]["membership_package_count"] == 1
    assert report["automatic_hub_ready_decision_allowed"] is False


def test_invalid_package_fails_closed(tmp_path, monkeypatch):
    approved = tmp_path / "approved"
    approved.mkdir()
    _write(
        approved / "bad.json",
        {
            "article_id": "BAD",
            "status": "approved",
            "site_category_key": "tzjq",
            "primary_seo_cluster_id": "made_up",
        },
    )

    def reject(primary, secondary):
        raise ValueError("unknown primary SEO cluster id: made_up")

    monkeypatch.setattr("engine.hub_readiness.normalize_seo_cluster_assignment", reject)
    report = audit_hub_readiness(
        approved_dir=approved,
        registry_rows=[],
        allowed_clusters=ALLOWED,
    )
    assert report["ok"] is False
    assert report["formal_approved_package_count"] == 1
    assert report["transport_inventory_valid"] is False
    assert report["errors"] == ["unknown primary SEO cluster id: made_up"]


def test_duplicate_article_id_in_formal_inventory_fails_closed(tmp_path, monkeypatch):
    approved = tmp_path / "approved"
    approved.mkdir()
    base = {
        "article_id": "A1",
        "status": "approved",
        "site_category_key": "tzjq",
    }
    _write(approved / "a.json", base)
    _write(approved / "b.json", base)
    monkeypatch.setattr("engine.hub_readiness.normalize_seo_cluster_assignment", lambda primary, secondary: (None, []))
    report = audit_hub_readiness(
        approved_dir=approved,
        registry_rows=[],
        allowed_clusters=ALLOWED,
    )
    assert report["ok"] is False
    assert any("duplicate article_id" in error for error in report["errors"])
