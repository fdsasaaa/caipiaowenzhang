from __future__ import annotations

import copy

import pytest

from engine.formal_approved_inventory import FormalInventoryError, stage_formal_approved_package
from engine.text import sha256_text


def _package() -> dict:
    content = "<p>这是经过审核的正式测试正文。</p>" * 30
    return {
        "article_id": "LCM-FORMAL-001",
        "title": "分分彩测试文章",
        "seo_title": "分分彩测试文章",
        "slug": "ffc-formal-001",
        "meta_description": "用于验证正式 Approved Package 库存入库。",
        "primary_keyword": "分分彩测试文章",
        "secondary_keywords": [],
        "search_intent": "测试正式库存入库",
        "category": "投注机巧",
        "site_category_key": "tzjq",
        "content_type": "technique_article",
        "content_format": "html",
        "content": content,
        "rule_refs": ["R1"],
        "source_refs": ["S1"],
        "case_scope": "mechanics_only",
        "fingerprint": "fp-formal-001",
        "content_hash": sha256_text(content),
        "status": "approved",
        "primary_seo_cluster_id": "ffc_research",
        "secondary_seo_cluster_ids": ["research_lab"],
    }


def test_stage_new_package_and_repeat_is_idempotent(tmp_path):
    package = _package()
    first = stage_formal_approved_package(package, approved_root=tmp_path)
    second = stage_formal_approved_package(package, approved_root=tmp_path)
    assert first["status"] == "staged"
    assert second["status"] == "unchanged"
    assert (tmp_path / "LCM-FORMAL-001.json").is_file()


def test_same_id_different_content_hash_requires_revision(tmp_path):
    package = _package()
    stage_formal_approved_package(package, approved_root=tmp_path)
    changed = copy.deepcopy(package)
    changed["content"] += "<p>正文修订。</p>"
    changed["content_hash"] = sha256_text(changed["content"])
    with pytest.raises(FormalInventoryError, match="different content_hash"):
        stage_formal_approved_package(changed, approved_root=tmp_path)


def test_same_id_same_content_but_different_metadata_is_not_silent_overwrite(tmp_path):
    package = _package()
    stage_formal_approved_package(package, approved_root=tmp_path)
    changed = copy.deepcopy(package)
    changed["seo_title"] = "修改后的 SEO 标题"
    with pytest.raises(FormalInventoryError, match="different approved metadata"):
        stage_formal_approved_package(changed, approved_root=tmp_path)


def test_unapproved_package_is_rejected(tmp_path):
    package = _package()
    package["status"] = "draft"
    with pytest.raises(FormalInventoryError, match="status must be approved"):
        stage_formal_approved_package(package, approved_root=tmp_path)


def test_content_hash_must_match(tmp_path):
    package = _package()
    package["content_hash"] = "0" * 64
    with pytest.raises(FormalInventoryError, match="content_hash does not match"):
        stage_formal_approved_package(package, approved_root=tmp_path)


def test_site_category_must_match_content_type(tmp_path):
    package = _package()
    package["site_category_key"] = "gjfa"
    with pytest.raises(FormalInventoryError, match="site_category_key mismatch"):
        stage_formal_approved_package(package, approved_root=tmp_path)


def test_unknown_cluster_fails_closed_with_normalized_error(tmp_path):
    package = _package()
    package["primary_seo_cluster_id"] = "made_up"
    with pytest.raises(FormalInventoryError, match="unknown primary SEO cluster id"):
        stage_formal_approved_package(package, approved_root=tmp_path)
