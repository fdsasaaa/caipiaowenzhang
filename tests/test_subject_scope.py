from types import SimpleNamespace

from engine import approval, blueprints, dedup
from engine.article_memory import get_article_record
from engine.draft_packets import DraftReview, build_draft_packet, review_draft


def _plan():
    return {
        "provider_id": "generic-format",
        "lottery": "通用五位数",
        "play": "前三直选",
        "subject_lottery": "分分彩",
        "subject_play": "前三直选",
        "technique_family": "F-SUBJECT",
        "technique_atoms": ["sum_range"],
        "positions": ["百位", "十位", "个位"],
        "source_refs": ["S1"],
        "source_support_count": 1,
        "source_risk_rate": 0.0,
        "status": "ready_mechanics_only",
        "rule_refs": ["R1"],
        "allowed_case_scope": "mechanics_only",
        "case_plan": {
            "supported": [{"atom": "sum_range", "metric": "digit_sum"}],
            "unsupported": [],
            "case_engine_ready": True,
        },
    }


def test_blueprint_separates_subject_from_rule_scope(monkeypatch):
    monkeypatch.setattr(blueprints, "duplicate_candidates", lambda candidate: [])
    bp = blueprints.blueprint_from_plan(_plan())
    assert bp["lottery"] == "通用五位数"
    assert bp["play"] == "前三直选"
    assert bp["subject_lottery"] == "分分彩"
    assert bp["subject_play"] == "前三直选"
    assert bp["title"].startswith("分分彩前三直选技巧")
    assert bp["primary_keyword"] == "分分彩前三直选和值技巧"


def test_draft_packet_freezes_subject_and_rejects_tampering(monkeypatch):
    monkeypatch.setattr(blueprints, "duplicate_candidates", lambda candidate: [])
    bp = blueprints.blueprint_from_plan(_plan())
    packet = build_draft_packet(bp)
    assert packet["immutable_facts"]["lottery"] == "通用五位数"
    assert packet["immutable_facts"]["subject_lottery"] == "分分彩"

    article = {
        "article_id": bp["article_id"],
        "title": packet["seo"]["title"],
        "slug": "subject-scope-test",
        "meta_description": packet["seo"]["meta_description"],
        "primary_keyword": packet["seo"]["primary_keyword"],
        "search_intent": packet["seo"]["search_intent"],
        "summary": "摘要",
        "content": "<p>演示数据，不是真实开奖记录。这里是规则说明。</p>",
        "content_format": "html",
        "site_category_key": "tzjq",
        "subject_lottery": "另一个彩种",
        "rule_refs": ["R1"],
        "case_scope": "mechanics_only",
        "status": "draft",
    }
    report = review_draft(packet, article)
    assert report.passed is False
    assert any("subject_lottery differs" in error for error in report.errors)


def test_approval_package_carries_subject_without_changing_rule_scope(monkeypatch):
    packet = {
        "article_id": "A-SUBJECT",
        "blueprint_id": "BP-SUBJECT",
        "immutable_facts": {
            "provider_id": "generic-format",
            "lottery": "通用五位数",
            "play": "前三直选",
            "subject_lottery": "分分彩",
            "subject_play": "前三直选",
            "content_type": "technique_article",
            "site_category_key": "tzjq",
            "content_format": "html",
            "technique_family": "F-SUBJECT",
            "technique_atoms": ["sum_range"],
            "rule_refs": ["R1"],
            "source_refs": ["S1"],
            "case_scope": "mechanics_only",
            "fingerprint": "FP-SUBJECT",
            "case_structure": "selector=前三;metrics=sum",
        },
        "seo": {
            "title": "分分彩前三直选技巧：和值案例",
            "slug_seed": "subject-scope",
            "primary_keyword": "分分彩前三直选技巧",
            "secondary_keywords": ["分分彩技巧"],
            "search_intent": "学习具体投注技巧并看懂可复算案例",
        },
        "output_contract": {"required_fields": []},
    }
    article = {
        "article_id": "A-SUBJECT",
        "title": "分分彩前三直选技巧：和值案例",
        "slug": "subject-scope",
        "meta_description": "测试描述",
        "primary_keyword": "分分彩前三直选技巧",
        "secondary_keywords": ["分分彩技巧"],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "summary": "摘要",
        "content": "<p>规则解释与案例。</p>" * 40,
        "rule_refs": ["R1"],
        "case_scope": "mechanics_only",
        "status": "draft",
    }
    monkeypatch.setattr(approval, "get_article_record", lambda article_id: {})
    monkeypatch.setattr(approval, "review_draft", lambda p, a: DraftReview(True, [], []))
    monkeypatch.setattr(approval, "evaluate_quality", lambda a: SimpleNamespace(passed=True, score=95, errors=[], warnings=[]))
    result = approval.evaluate_for_approval(packet, article)
    assert result.approved is True
    assert result.publish_package["lottery"] == "通用五位数"
    assert result.publish_package["subject_lottery"] == "分分彩"
    assert result.publish_package["subject_play"] == "前三直选"


def test_dedup_uses_subject_even_when_rule_scope_is_null(monkeypatch):
    old = {
        "article_id": "OLD",
        "title": "分分彩前三直选和值筛选",
        "primary_keyword": "分分彩前三直选技巧",
        "search_intent": "学习技巧",
        "lottery": None,
        "play": None,
        "subject_lottery": "分分彩",
        "subject_play": "前三直选",
        "technique_atoms": ["sum_range"],
        "case_structure": "sum-demo",
    }
    candidate = dict(old, article_id="NEW")
    monkeypatch.setattr(dedup, "iter_registry", lambda kind: iter([old]))
    hits = dedup.duplicate_candidates(candidate)
    assert hits and hits[0].article_id == "OLD"


def test_smoke_registry_effective_state_has_subject_migration():
    record = get_article_record("LCM-SMOKE-20260811-01")
    assert record is not None
    assert record["lottery"] is None
    assert record["subject_lottery"] == "分分彩"
    assert record["subject_play"] == "前三直选"
