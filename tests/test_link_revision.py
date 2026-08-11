import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from engine import approval, link_revision
from engine.draft_packets import DraftReview
from engine.internal_links import plan_internal_links
from engine.text import sha256_text

ROOT = Path(__file__).resolve().parents[1]


def _package():
    content = "<p>演示数据，不是真实开奖记录。这里是原始已批准正文。</p>" * 20
    return {
        "article_id": "A-REV",
        "status": "approved",
        "title": "分分彩定位胆冷热技巧：测试",
        "seo_title": "分分彩定位胆冷热技巧：测试",
        "slug": "revision-test",
        "meta_description": "测试描述",
        "primary_keyword": "分分彩定位胆冷热技巧",
        "secondary_keywords": ["定位胆冷热"],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "summary": "摘要",
        "category": "投注技巧",
        "site_category_key": "tzjq",
        "content_type": "technique_article",
        "content_format": "html",
        "tags": ["分分彩定位胆"],
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
        "fingerprint": "f" * 64,
        "content_hash": sha256_text(content),
    }


def _resolved_plan(url="https://www.laocaimi.org/article/target"):
    return {
        "article_id": "A-REV",
        "min_score": 45,
        "targets": [
            {
                "target_article_id": "TARGET-1",
                "anchor_hint": "分分彩定位胆遗漏技巧",
                "score": 90,
                "reasons": ["same_subject_play"],
                "resolution_status": "resolved",
                "url": url,
            }
        ],
    }


def _packet():
    return {
        "article_id": "A-REV",
        "blueprint_id": "BP-REV",
        "immutable_facts": {
            "provider_id": None,
            "lottery": "时时彩",
            "play": "定位胆",
            "subject_lottery": "分分彩",
            "subject_play": "定位胆",
            "content_type": "technique_article",
            "site_category_key": "tzjq",
            "content_format": "html",
            "technique_family": "F-REV",
            "technique_atoms": ["cold_hot_split"],
            "rule_refs": ["R1"],
            "source_refs": ["S1"],
            "case_scope": "mechanics_only",
            "fingerprint": "f" * 64,
            "case_structure": "selector=个位;metrics=frequency;scope=mechanics_only",
        },
        "seo": {
            "title": "分分彩定位胆冷热技巧：测试",
            "slug_seed": "revision-test",
            "primary_keyword": "分分彩定位胆冷热技巧",
            "secondary_keywords": ["定位胆冷热"],
            "search_intent": "学习具体投注技巧并看懂可复算案例",
        },
        "output_contract": {"required_fields": []},
    }


def test_revision_changes_content_hash_but_stays_draft():
    package = _package()
    revision = link_revision.build_internal_link_revision(package, _resolved_plan())
    assert revision["status"] == "draft"
    assert revision["revision_reason"] == "internal_links"
    assert revision["revision_of_content_hash"] == package["content_hash"]
    assert revision["proposed_content_hash"] != package["content_hash"]
    assert 'data-lcm-related-reading="1"' in revision["content"]
    assert 'href="https://www.laocaimi.org/article/target"' in revision["content"]
    assert revision["internal_links"] == [{
        "target_article_id": "TARGET-1",
        "anchor": "分分彩定位胆遗漏技巧",
        "url": "https://www.laocaimi.org/article/target",
    }]


def test_current_eight_drafts_cannot_be_revised_before_any_target_is_published():
    package = json.loads((ROOT / "smoke/batch2/approved/LCM-IDEA-48eb8743fbbbad11.json").read_text(encoding="utf-8"))
    plan = plan_internal_links(package["article_id"], limit=3)
    assert plan["targets"]
    assert all(target["resolution_status"] == "pending_published_url" for target in plan["targets"])
    with pytest.raises(ValueError, match="at least one resolved target URL"):
        link_revision.build_internal_link_revision(package, plan)


def test_revision_rejects_tampered_approved_package_hash():
    package = _package()
    package["content"] += "tampered"
    with pytest.raises(ValueError, match="content_hash does not match"):
        link_revision.build_internal_link_revision(package, _resolved_plan())


@pytest.mark.parametrize(
    "url, message",
    [
        ("http://www.laocaimi.org/article/a", "must use https"),
        ("https://evil.example/article/a", "host is not allowed"),
        ("https://www.laocaimi.org/article/a?ref=x", "without query or fragment"),
        ("https://www.laocaimi.org/article/a#part", "without query or fragment"),
        ("https://user:pass@www.laocaimi.org/article/a", "must not contain credentials"),
    ],
)
def test_revision_rejects_noncanonical_or_external_urls(url, message):
    with pytest.raises(ValueError, match=message):
        link_revision.build_internal_link_revision(_package(), _resolved_plan(url))


def test_revision_escapes_anchor_and_limits_links():
    package = _package()
    plan = _resolved_plan()
    plan["targets"] = [
        {
            "target_article_id": f"TARGET-{i}",
            "anchor_hint": "<b>技巧</b>" if i == 1 else f"技巧{i}",
            "score": 90 - i,
            "reasons": ["same_subject_play"],
            "resolution_status": "resolved",
            "url": f"https://www.laocaimi.org/article/{i}",
        }
        for i in range(1, 5)
    ]
    revision = link_revision.build_internal_link_revision(package, plan, max_links=3)
    assert len(revision["internal_links"]) == 3
    assert "&lt;b&gt;技巧&lt;/b&gt;" in revision["content"]
    assert "<b>技巧</b>" not in revision["content"]
    assert "https://www.laocaimi.org/article/4" not in revision["content"]


def test_reapproval_preserves_revision_ancestry(monkeypatch):
    revision = link_revision.build_internal_link_revision(_package(), _resolved_plan())
    monkeypatch.setattr(approval, "get_article_record", lambda article_id: {})
    monkeypatch.setattr(approval, "keyword_owners", lambda keyword, exclude_article_id=None: [])
    monkeypatch.setattr(approval, "review_draft", lambda packet, article: DraftReview(True, [], []))
    monkeypatch.setattr(approval, "evaluate_quality", lambda article: SimpleNamespace(passed=True, score=95, errors=[], warnings=[]))
    result = approval.evaluate_for_approval(_packet(), revision)
    assert result.approved is True
    assert result.publish_package["revision_reason"] == "internal_links"
    assert result.publish_package["revision_of_content_hash"] == _package()["content_hash"]
    assert result.publish_package["content_hash"] == revision["proposed_content_hash"]
    assert result.registry_record["revision_reason"] == "internal_links"
    assert result.registry_record["revision_of_content_hash"] == _package()["content_hash"]
