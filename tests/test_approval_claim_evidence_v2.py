from types import SimpleNamespace

from engine import approval
from engine.draft_packets import DraftReview


def _packet():
    return {
        "article_id": "A-CLAIM",
        "blueprint_id": "BP-CLAIM",
        "immutable_facts": {
            "provider_id": None,
            "lottery": None,
            "play": None,
            "subject_lottery": "分分彩",
            "subject_play": "后二直选",
            "content_type": "technique_article",
            "site_category_key": "tzjq",
            "content_format": "html",
            "technique_family": "F1",
            "technique_atoms": ["position_filter"],
            "rule_refs": ["R1"],
            "source_refs": ["S1"],
            "case_scope": "mechanics_only",
            "fingerprint": "1" * 64,
            "case_structure": "selector=后二;metrics=position_filter;scope=mechanics_only",
            "information_gain_type": "method_mechanics_and_reproducible_case",
        },
        "seo": {
            "primary_keyword": "分分彩后二直选技巧",
            "secondary_keywords": [],
            "search_intent": "学习具体投注技巧并看懂可复算案例",
        },
    }


def _article(entries):
    return {
        "article_id": "A-CLAIM",
        "title": "分分彩后二直选技巧：如何理解注数",
        "slug": "ffc-houer-direct",
        "meta_description": "解释后二直选的结果空间和注数。",
        "primary_keyword": "分分彩后二直选技巧",
        "secondary_keywords": [],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "summary": "说明规则",
        "category": "投注技巧",
        "site_category_key": "tzjq",
        "content_type": "technique_article",
        "content_format": "html",
        "tags": [],
        "content": "<p>演示数据，不是真实开奖记录。</p><p>后二直选理论结果空间共100注。</p>" + "<p>这里只解释组合空间，不讨论未来预测。</p>" * 15,
        "rule_refs": ["R1"],
        "source_refs": ["S1"],
        "case_scope": "mechanics_only",
        "status": "draft",
        "generation_contract_version": "2.0",
        "claim_evidence": entries,
    }


def _isolate_other_gates(monkeypatch):
    monkeypatch.setattr(approval, "get_article_record", lambda article_id: {})
    monkeypatch.setattr(approval, "keyword_owners", lambda keyword, exclude_article_id=None: [])
    monkeypatch.setattr(approval, "review_draft", lambda packet, article: DraftReview(True, [], []))
    monkeypatch.setattr(approval, "evaluate_quality", lambda article: SimpleNamespace(passed=True, score=95, errors=[], warnings=[]))


def test_approval_rejects_v2_hard_claim_without_evidence(monkeypatch):
    _isolate_other_gates(monkeypatch)
    result = approval.evaluate_for_approval(_packet(), _article([]))
    assert result.approved is False
    assert any("hard claim sentence lacks claim_evidence" in e for e in result.errors)


def test_approval_preserves_v2_evidence_in_approved_package(monkeypatch):
    _isolate_other_gates(monkeypatch)
    entries = [{
        "claim_text": "后二直选理论结果空间共100注",
        "claim_type": "rule_fact",
        "support_type": "verified_rule",
        "support_refs": ["R1"],
        "evidence_note": "由已验证玩法规则支持",
    }]
    result = approval.evaluate_for_approval(_packet(), _article(entries))
    assert result.approved is True
    assert result.publish_package["generation_contract_version"] == "2.0"
    assert result.publish_package["claim_evidence"] == entries
    assert result.registry_record["claim_evidence"] == entries
