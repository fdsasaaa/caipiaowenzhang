from types import SimpleNamespace

from engine import approval
from engine.draft_packets import DraftReview


def _packet():
    return {
        "article_id": "A1",
        "blueprint_id": "BP1",
        "immutable_facts": {
            "provider_id": "p1",
            "lottery": "时时彩",
            "play": "后三直选",
            "content_type": "technique_article",
            "site_category_key": "tzjq",
            "content_format": "html",
            "technique_family": "F1",
            "technique_atoms": ["sum_range"],
            "rule_refs": ["R1"],
            "source_refs": ["S1"],
            "case_scope": "mechanics_only",
        },
        "seo": {
            "title": "时时彩后三直选技巧：和值案例",
            "slug_seed": "ssc-last3-sum",
            "primary_keyword": "时时彩后三直选技巧",
            "secondary_keywords": ["时时彩技巧"],
            "search_intent": "学习具体投注技巧并看懂可复算案例",
        },
        "output_contract": {"required_fields": []},
    }


def _article():
    return {
        "article_id": "A1",
        "title": "时时彩后三直选技巧：和值案例",
        "slug": "ssc-last3-sum",
        "meta_description": "一个清晰、可复算的时时彩后三直选技巧案例说明。",
        "primary_keyword": "时时彩后三直选技巧",
        "secondary_keywords": ["时时彩技巧"],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "summary": "摘要",
        "content": "<p>演示数据，不是真实开奖记录。</p>" + "<p>这里解释玩法规则、和值计算和案例限制。</p>" * 30,
        "content_format": "html",
        "site_category_key": "tzjq",
        "rule_refs": ["R1"],
        "case_scope": "mechanics_only",
        "status": "draft",
    }


def test_approved_package_inherits_reserved_fingerprint_and_site_contract(monkeypatch):
    monkeypatch.setattr(approval, "get_article_record", lambda article_id: {
        "article_id": "A1", "fingerprint": "FP-ORIGINAL", "case_structure": "selector=后三;metrics=sum",
        "information_gain_type": "method_mechanics_and_reproducible_case", "technique_atoms": ["sum_range"],
        "content_type": "technique_article", "site_category_key": "tzjq", "content_format": "html"
    })
    monkeypatch.setattr(approval, "review_draft", lambda packet, article: DraftReview(True, [], []))
    monkeypatch.setattr(approval, "evaluate_quality", lambda article: SimpleNamespace(passed=True, score=95, errors=[], warnings=[]))
    result = approval.evaluate_for_approval(_packet(), _article())
    assert result.approved is True
    assert result.publish_package["fingerprint"] == "FP-ORIGINAL"
    assert result.publish_package["content_type"] == "technique_article"
    assert result.publish_package["site_category_key"] == "tzjq"
    assert result.publish_package["content_format"] == "html"
    assert result.publish_package["summary"] == "摘要"
    assert result.publish_package["status"] == "approved"


def test_failed_draft_never_gets_publish_package(monkeypatch):
    monkeypatch.setattr(approval, "get_article_record", lambda article_id: {"article_id": "A1", "fingerprint": "FP"})
    monkeypatch.setattr(approval, "review_draft", lambda packet, article: DraftReview(False, ["bad draft"], []))
    monkeypatch.setattr(approval, "evaluate_quality", lambda article: SimpleNamespace(passed=True, score=95, errors=[], warnings=[]))
    result = approval.evaluate_for_approval(_packet(), _article())
    assert result.approved is False
    assert result.status == "rejected_for_revision"
    assert result.publish_package is None
