from __future__ import annotations

import json

import pytest

from engine.ai_generation import GenerationError
from engine.approval import evaluate_for_approval
from engine.real_group6_ai_generation import generate_real_group6_article
from engine.real_group6_article_contract import (
    DOMAIN_BOUNDARY,
    PRIMARY_KEYWORD,
    SOURCE_BOUNDARY,
    build_real_group6_article_packet,
    evaluate_real_group6_article,
)
from scripts.real_group6_live_article import EXPECTED, build_preflight_summary

# Real one-shot acceptance: resp_06759b5457ac444d016a7cf9fbeae48196a703bd16e3bcb033.
# The fake transport remains the permanent network-free regression path after paid cleanup.


def _model_article(packet: dict) -> dict:
    content = (
        f"<p>{SOURCE_BOUNDARY}</p>"
        f"<p>{DOMAIN_BOUNDARY}</p>"
        "<p><strong>演示数据，不是真实开奖记录。</strong></p>"
        "<h2>组六到底是什么</h2>"
        "<p>分分彩后三组六要求三个数字互不相同。无序集合{1,2,3}只算一个组六投注单位，"
        "对应6个有序排列：123、132、213、231、312、321。</p>"
        "<p>完整组六域有120个无序单位，对应720个组六结构的有序结果；全部三位有序结果是1000个。"
        "这里的72%只用于解释结构分区，不代表命中率、胜率或盈利能力。</p>"
        "<p>如果把120个单位全部使用，就是120/120=100%的组六目标域覆盖，超过项目90%的执行上限，"
        "所以这篇文章只解释玩法域，不生成全域投注。</p>"
        "<p>112属于组三：两位相同、一位不同；777是三同号，既不是组六也不是组三。</p>"
        "<h2>实际怎么操作</h2>"
        "<ol><li>固定分分彩后三组六。</li><li>确认三个数字互不相同。</li>"
        "<li>把相同三数字的不同排列归到同一个无序单位。</li><li>用123的六个排列核对。</li>"
        "<li>解释到玩法域、结构占比与覆盖率分母后停止，不输出投注子集。</li></ol>"
    )
    return {
        "article_id": packet["article_id"],
        "title": "分分彩后三组六技巧：120个组选单位和720种排列怎么理解",
        "seo_title": "分分彩后三组六技巧：120个组选单位和720种排列怎么理解",
        "slug": "ffc-last3-group6-120-units-720-orders",
        "meta_description": "分分彩后三组六技巧案例：解释120个无序组选单位、720种有序排列，以及结构占比和目标玩法覆盖率的区别。",
        "primary_keyword": PRIMARY_KEYWORD,
        "secondary_keywords": ["分分彩组六", "后三组六", "组六投注技巧", "组六号码结构"],
        "search_intent": packet["seo"]["search_intent"],
        "summary": "用可复算示例解释组六投注单位、六种排列、完整玩法域和90%内部执行门禁。",
        "category": "投注技巧",
        "site_category_key": "tzjq",
        "content_type": "technique_article",
        "content_format": "html",
        "tags": ["分分彩", "后三组六", "组六结构"],
        "content": content,
        "rule_refs": ["SSC-HIST-MECH-3STAR-GROUP6-V1"],
        "source_refs": ["BRBCW-004115"],
        "case_scope": "mechanics_only",
        "status": "draft",
        "generation_contract_version": "2.0",
        "claim_evidence": [
            {
                "claim_text": "分分彩后三组六要求三个数字互不相同。",
                "claim_type": "rule_fact",
                "support_type": "verified_rule",
                "support_refs": ["SSC-HIST-MECH-3STAR-GROUP6-V1"],
                "evidence_note": "verified group6 mechanics",
            },
            {
                "claim_text": "演示数据，不是真实开奖记录。",
                "claim_type": "editorial",
                "support_type": "synthetic_case",
                "support_refs": ["case_bundle"],
                "evidence_note": "synthetic disclosure",
            },
        ],
        "editorial_contract_version": "1.1",
        "practical_guidance": {
            "steps": [
                "固定分分彩后三组六。",
                "确认三个数字互不相同。",
                "将不同排列归到一个无序单位。",
                "用123的六个排列核对。",
                "解释完玩法域与覆盖率分母后停止。",
            ],
            "starting_space": "120个组六无序投注单位",
            "after_primary_filter_space": "不做投注过滤；本文只解释完整组六玩法域",
            "parameter_freeze_rule": "组六是系统在查看演示样本前预冻结的验证模式。",
            "stop_condition": "解释到玩法域和确定性示例后停止，不输出实际投注子集。",
            "next_step_policy": "只有新增条件具有已验证规则或证据并可复算时，才允许另起实际投注合同；该合同还必须选择不超过90%的组六目标域，并重新通过金额和经济参数门禁。",
        },
    }


def _response(article: dict) -> dict:
    return {
        "id": "resp_group6_offline_fake",
        "status": "completed",
        "output": [{
            "type": "message",
            "content": [{"type": "output_text", "text": json.dumps(article, ensure_ascii=False)}],
        }],
    }


def test_live_preflight_is_exactly_locked_and_non_publishing():
    summary = build_preflight_summary()
    assert summary["ok"] is True
    for key, value in EXPECTED.items():
        assert summary[key] == value
    assert summary["provider_call"] is False
    assert summary["registry_write"] is False
    assert summary["website_write"] is False
    assert summary["scheduled"] is False
    assert summary["published"] is False


def test_fake_transport_exercises_structured_schema_and_full_acceptance_without_network():
    packet = build_real_group6_article_packet()
    model_article = _model_article(packet)
    observed = {}

    def transport(url, headers, payload, timeout):
        observed["url"] = url
        observed["headers"] = headers
        observed["payload"] = payload
        observed["timeout"] = timeout
        return _response(model_article)

    generated = generate_real_group6_article(
        packet,
        model="gpt-5.4-mini",
        api_key="test-key",
        transport=transport,
    )

    support_enum = observed["payload"]["text"]["format"]["schema"]["properties"]["claim_evidence"]["items"]["properties"]["support_type"]["enum"]
    assert "policy_contract" in support_enum
    assert "72%" in observed["payload"]["input"]
    assert "120/120=100%" in observed["payload"]["input"]
    assert generated.response_id == "resp_group6_offline_fake"
    assert generated.article["content"] == model_article["content"]

    support_types = {row["support_type"] for row in generated.article["claim_evidence"]}
    assert "source_unverified" in support_types
    assert "verified_rule" in support_types
    assert "policy_contract" in support_types

    approval = evaluate_for_approval(packet, generated.article)
    custom = evaluate_real_group6_article(generated.article)
    assert approval.approved is True, approval.errors
    assert approval.quality_score == 100
    assert approval.editorial_score == 100
    assert custom.passed is True, custom.errors
    assert custom.score == 100


def test_generator_refuses_contract_drift_before_transport():
    packet = build_real_group6_article_packet()
    packet["real_group6_validation"]["full_domain_executable_portfolio_allowed"] = True
    called = False

    def transport(url, headers, payload, timeout):
        nonlocal called
        called = True
        return {}

    with pytest.raises(GenerationError, match="full-domain execution"):
        generate_real_group6_article(
            packet,
            model="gpt-5.4-mini",
            api_key="test-key",
            transport=transport,
        )
    assert called is False


def test_evidence_normalization_never_rewrites_model_content():
    packet = build_real_group6_article_packet()
    model_article = _model_article(packet)
    original = model_article["content"]

    generated = generate_real_group6_article(
        packet,
        model="gpt-5.4-mini",
        api_key="test-key",
        transport=lambda *_args: _response(model_article),
    )
    assert generated.article["content"] == original
