import json

import pytest

from engine.ai_generation import GenerationError, RESPONSES_URL, generate_article


def _packet():
    return {
        "article_id": "A-AUTO",
        "status": "ready_for_ai_draft",
        "immutable_facts": {
            "provider_id": None,
            "lottery": None,
            "play": None,
            "subject_lottery": "分分彩",
            "subject_play": "定位胆",
            "content_type": "technique_article",
            "site_category_key": "tzjq",
            "content_format": "html",
            "technique_family": "F1",
            "technique_atoms": ["omission_threshold"],
            "rule_refs": ["R1"],
            "source_refs": ["S1"],
            "case_scope": "mechanics_only",
            "fingerprint": "f" * 64,
            "case_structure": "selector=个位;metrics=omission;scope=mechanics_only",
            "information_gain_type": "method_mechanics_and_reproducible_case",
        },
        "seo": {
            "title": "分分彩定位胆遗漏技巧：案例",
            "primary_keyword": "分分彩定位胆遗漏技巧",
            "secondary_keywords": ["定位胆遗漏"],
            "search_intent": "学习具体投注技巧并看懂可复算案例",
        },
        "case_bundle": {"must_label_as": "演示数据，不是真实开奖记录", "draws": ["12345"]},
    }


def _article():
    return {
        "article_id": "A-AUTO",
        "title": "分分彩定位胆遗漏技巧：案例",
        "seo_title": "分分彩定位胆遗漏技巧：案例",
        "slug": "ffc-dingweidan-omission",
        "meta_description": "用简单案例解释定位胆遗漏的计算方式。",
        "primary_keyword": "分分彩定位胆遗漏技巧",
        "secondary_keywords": ["定位胆遗漏"],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "summary": "解释遗漏如何计算，不把历史等待时间写成预测结论。",
        "category": "投注技巧",
        "site_category_key": "tzjq",
        "content_type": "technique_article",
        "content_format": "html",
        "tags": ["分分彩", "定位胆遗漏"],
        "content": "<p>演示数据，不是真实开奖记录。</p>" + "<p>这里只说明遗漏距离的计算方法，不代表下一期更容易出现。</p>" * 12,
        "rule_refs": ["R1"],
        "source_refs": ["S1"],
        "case_scope": "mechanics_only",
        "status": "draft",
        "generation_contract_version": "2.0",
        "claim_evidence": [],
    }


def test_generation_uses_responses_structured_output_and_validates_identity():
    seen = {}
    def fake_transport(url, headers, payload, timeout):
        seen.update(url=url, headers=headers, payload=payload, timeout=timeout)
        return {
            "id": "resp_test",
            "status": "completed",
            "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(_article(), ensure_ascii=False)}]}],
        }
    result = generate_article(_packet(), model="gpt-5", api_key="test-key", transport=fake_transport)
    assert result.article["article_id"] == "A-AUTO"
    assert result.response_id == "resp_test"
    assert seen["url"] == RESPONSES_URL
    assert seen["headers"]["Authorization"] == "Bearer test-key"
    assert seen["payload"]["store"] is False
    fmt = seen["payload"]["text"]["format"]
    assert fmt["type"] == "json_schema"
    assert fmt["strict"] is True
    assert "claim_evidence" in fmt["schema"]["required"]


def test_generation_requires_api_key(monkeypatch):
    # The production contract intentionally falls back to OPENAI_API_KEY when
    # api_key is empty.  Isolate this negative-path test from GitHub Actions,
    # where a real provider credential is present for the daily production job.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(GenerationError, match="OPENAI_API_KEY"):
        generate_article(_packet(), api_key="", transport=lambda *args: {})


def test_generation_rejects_model_mutation_of_immutable_identity():
    article = _article()
    article["site_category_key"] = "gjfa"
    def fake_transport(url, headers, payload, timeout):
        return {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(article, ensure_ascii=False)}]}]}
    with pytest.raises(GenerationError, match="site_category_key"):
        generate_article(_packet(), api_key="test", transport=fake_transport)


def test_generation_rejects_incomplete_response_before_parsing_output():
    def fake_transport(url, headers, payload, timeout):
        return {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}, "output": []}
    with pytest.raises(GenerationError, match="not completed"):
        generate_article(_packet(), api_key="test", transport=fake_transport)


def test_generation_rejects_refusal_content():
    def fake_transport(url, headers, payload, timeout):
        return {
            "status": "completed",
            "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "cannot comply"}]}],
        }
    with pytest.raises(GenerationError, match="refused"):
        generate_article(_packet(), api_key="test", transport=fake_transport)
