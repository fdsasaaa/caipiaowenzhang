from __future__ import annotations

from engine import internal_links, link_revision, publication_receipts
from engine.text import sha256_text


def _target_current():
    return {
        "article_id": "TARGET-PUBLISHED",
        "status": "approved",
        "subject_lottery": "分分彩",
        "subject_play": "定位胆",
        "content_type": "technique_article",
        "primary_keyword": "分分彩定位胆遗漏技巧",
        "technique_atoms": ["omission_threshold", "position_filter"],
        "fingerprint": "a" * 64,
        "content_hash": "b" * 64,
        "website_draft_path": "content/drafts/target-published.json",
        "published_url": None,
    }


def _receipt():
    row = {
        "schema_version": 1,
        "receipt_type": "publication_receipt",
        "article_id": "TARGET-PUBLISHED",
        "article_key": "target-published",
        "fingerprint": "a" * 64,
        "content_hash": "b" * 64,
        "cms_id": 777,
        "published_url": "https://www.laocaimi.org/index.php?c=show&id=777",
        "published_at": "2026-08-11T14:30:00+00:00",
        "publisher_article_hash": "c" * 64,
        "source_file": "target-published.json",
        "site_base_url": "https://www.laocaimi.org",
    }
    row["receipt_id"] = publication_receipts.publication_receipt_id(row)
    return row


def _source_row():
    return {
        "article_id": "SOURCE-A",
        "status": "approved",
        "subject_lottery": "分分彩",
        "subject_play": "定位胆",
        "content_type": "technique_article",
        "primary_keyword": "分分彩定位胆冷热技巧",
        "technique_atoms": ["cold_hot_split"],
    }


def _source_package():
    content = "<p>演示数据，不是真实开奖记录。这里是待增加相关阅读的原始正文。</p>" * 20
    return {
        "article_id": "SOURCE-A",
        "status": "approved",
        "title": "分分彩定位胆冷热技巧：生命周期测试",
        "seo_title": "分分彩定位胆冷热技巧：生命周期测试",
        "slug": "source-a",
        "meta_description": "测试描述",
        "primary_keyword": "分分彩定位胆冷热技巧",
        "secondary_keywords": ["定位胆冷热"],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "summary": "摘要",
        "category": "投注技巧",
        "site_category_key": "tzjq",
        "content_type": "technique_article",
        "content_format": "html",
        "content": content,
        "internal_links": [],
        "rule_refs": ["R1"],
        "source_refs": ["S1"],
        "case_scope": "mechanics_only",
        "provider_id": None,
        "lottery": "时时彩",
        "play": "定位胆",
        "subject_lottery": "分分彩",
        "subject_play": "定位胆",
        "technique_atoms": ["cold_hot_split"],
        "fingerprint": "d" * 64,
        "content_hash": sha256_text(content),
    }


def test_publication_receipt_resolves_planner_target_and_unlocks_revision(monkeypatch):
    target_current = _target_current()
    monkeypatch.setattr(publication_receipts, "get_article_record", lambda article_id: target_current)
    imported = publication_receipts.import_publication_receipt(_receipt(), record=False)
    target_published = imported["registry_record"]
    assert target_published["status"] == "published"
    assert target_published["published_url"] == "https://www.laocaimi.org/index.php?c=show&id=777"

    rows = [_source_row(), target_published]
    monkeypatch.setattr(internal_links, "iter_registry", lambda kind: iter(rows))
    plan = internal_links.plan_internal_links("SOURCE-A", limit=3)
    assert plan["targets"][0]["target_article_id"] == "TARGET-PUBLISHED"
    assert plan["targets"][0]["resolution_status"] == "resolved"
    assert plan["targets"][0]["url"] == "https://www.laocaimi.org/index.php?c=show&id=777"

    revision = link_revision.build_internal_link_revision(_source_package(), plan)
    assert revision["status"] == "draft"
    assert revision["revision_reason"] == "internal_links"
    assert revision["revision_of_content_hash"] == _source_package()["content_hash"]
    assert revision["proposed_content_hash"] != _source_package()["content_hash"]
    assert 'href="https://www.laocaimi.org/index.php?c=show&amp;id=777"' in revision["content"]
