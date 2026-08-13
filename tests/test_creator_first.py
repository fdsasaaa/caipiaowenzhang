from __future__ import annotations

import json

import pytest

from engine.creator_first import (
    CreatorFirstError,
    build_creator_packet,
    build_creator_prompt,
    build_creator_request,
    generate_creator_article,
    validate_creator_output,
)
from engine.creator_style import evaluate_creator_style


def _ffc_mechanic(request: dict) -> dict:
    for row in request["available_mechanics"]:
        if row["reader_lottery"] == "分分彩":
            return row
    raise AssertionError("expected at least one verified FFC-compatible mechanic")


def _good_payload(request: dict) -> dict:
    mechanic = _ffc_mechanic(request)
    keyword = "分分彩轻量创作者独立技巧测试"
    content = (
        "<p>这篇只讲一个简单思路：先把玩法规则看清，再用一个自己能复算的小方法做观察。"
        "重点不是堆很多条件，而是每次只改变一个判断，让读者知道自己为什么留下这些候选。</p>"
        "<p>方法本身是创作出来的研究思路，不是官方规则，也不是已经证明有效的预测规律。"
        "真正固定不变的部分只有玩法机制；技巧怎么组合、什么时候不用继续加条件，都应该讲清楚。</p>"
        "<h2>怎么用</h2>"
        "<p>先确认当前玩法的基本结构，再选一个容易解释的观察条件。条件确定以后就按同一种方式复算，"
        "不要看到结果不满意就临时换标准。文章只演示思路，不讨论未经核验的平台奖金、赔率、返点或收益。</p>"
        "<p>如果后面想增加第二个条件，先问自己两个问题：它是不是有清楚的规则依据，读者能不能自己重复计算。"
        "两点都说不清，就不要为了显得复杂而继续叠加。这样的写法比套固定模板更容易让普通人看懂。</p>"
    )
    return {
        "manifest": {
            "selected_rule_ref": mechanic["rule_ref"],
            "subject_lottery": mechanic["reader_lottery"],
            "subject_play": mechanic["play"],
            "creation_mode": "technique",
            "technique_name": "单条件可复算观察法",
            "technique_tags": ["creator_single_condition_observation_z9"],
            "originality_note": "不是从候选池选题，而是从读者如何理解一个简单条件出发自由创作。",
            "reader_value": "让读者用很少的步骤理解一个技巧为什么这样设计。",
            "uses_draw_data": False,
            "uses_bankroll_design": False,
            "uses_staking_design": False,
            "bankroll_design_summary": "",
            "staking_design_summary": "",
            "case_label": "",
            "case_notes": [],
        },
        "article": {
            "article_id": request["article_id"],
            "title": keyword + "：一个条件讲清楚就够了",
            "seo_title": keyword + "：简单可复算思路",
            "slug": "ffc-creator-first-light-test-z9",
            "meta_description": keyword + "案例，用简单中文说明如何固定一个观察条件并保持可复算，不堆叠复杂过滤。",
            "primary_keyword": keyword,
            "secondary_keywords": ["分分彩技巧", "彩票技巧案例"],
            "search_intent": "学习一个简单、能自己复算的分分彩技巧设计思路",
            "summary": "用一个条件说明技巧设计、规则边界和停止继续叠加的方法。",
            "category": "投注技巧",
            "site_category_key": "tzjq",
            "content_type": "technique_article",
            "content_format": "html",
            "tags": ["分分彩", "投注技巧", "简单技巧"],
            "content": content,
            "rule_refs": [mechanic["rule_ref"]],
            "source_refs": [],
            "case_scope": "mechanics_only",
            "status": "draft",
            "generation_contract_version": "2.0",
            "claim_evidence": [],
        },
    }


def _response(payload: dict) -> dict:
    return {
        "id": "resp_creator_first_fake",
        "status": "completed",
        "output": [{
            "type": "message",
            "content": [{"type": "output_text", "text": json.dumps(payload, ensure_ascii=False)}],
        }],
    }


def test_creator_request_has_memory_and_rules_but_no_planner_or_angle_contract():
    request = build_creator_request(request_id="test001")
    assert request["article_id"] == "LCM-CREATOR-test001"
    assert request["available_mechanics"]
    assert "candidate_capacity" not in request
    assert "candidates" not in request
    assert "article_angle_contract" not in request
    assert request["automatic_retry"] is False
    prompt = build_creator_prompt(request)
    assert "existing_article_memory 只是长期记忆" in prompt
    assert "系统不替你指定技巧角度" in prompt
    assert "不要写成流水线报告" in prompt


def test_creator_packet_is_thin_and_reuses_existing_hard_gates():
    request = build_creator_request(request_id="test002")
    payload = _good_payload(request)
    packet = build_creator_packet(request, payload["manifest"], payload["article"])
    assert packet["creator_first_contract_version"] == "1.0"
    assert packet["immutable_facts"]["information_gain_type"] == "creator_original"
    assert packet["immutable_facts"]["angle_contract_verified"] is False
    assert "article_angle_contract_version" not in packet
    assert "editorial_contract_version" not in packet
    assert "practicality" not in packet
    assert packet["claims"]["economics_allowed"] is False
    assert packet["compliance"]["policy_ref"] == "USER-BET-COMPLIANCE-90-V1"


def test_creator_good_article_passes_existing_approval_and_human_style():
    request = build_creator_request(request_id="test003")
    result = validate_creator_output(request, _good_payload(request))
    assert result.approval.approved is True, result.approval.errors
    assert result.style.passed is True, result.style.errors
    assert result.approved is True, result.errors
    assert result.approval.quality_score >= 80
    assert result.approval.editorial_score == 100
    assert result.approval.angle_score is None


def test_fake_transport_makes_exactly_one_free_creator_request_path():
    request = build_creator_request(request_id="test004")
    payload = _good_payload(request)
    calls = []

    def transport(url, headers, body, timeout):
        calls.append((url, body, timeout))
        assert body["store"] is False
        assert body["text"]["format"]["name"] == "laocaimi_creator_first_v1"
        assert "candidate_capacity" not in body["input"]
        return _response(payload)

    result = generate_creator_article(
        request,
        model="gpt-5.4-mini",
        api_key="test-key",
        transport=transport,
    )
    assert len(calls) == 1
    assert result.response_id == "resp_creator_first_fake"
    assert result.article["provider_response_id"] == "resp_creator_first_fake"
    assert result.approved is True, result.errors


def test_creator_rejects_invented_rule_ref():
    request = build_creator_request(request_id="test005")
    payload = _good_payload(request)
    payload["manifest"]["selected_rule_ref"] = "MADE-UP-RULE"
    payload["article"]["rule_refs"] = ["MADE-UP-RULE"]
    with pytest.raises(CreatorFirstError, match="selected_rule_ref"):
        validate_creator_output(request, payload)


def test_creator_rejects_claimed_draw_data_when_none_was_supplied():
    request = build_creator_request(request_id="test006")
    payload = _good_payload(request)
    payload["manifest"]["uses_draw_data"] = True
    with pytest.raises(CreatorFirstError, match="draw-data"):
        validate_creator_output(request, payload)


def test_creator_synthetic_evidence_requires_visible_case_label():
    request = build_creator_request(request_id="test007")
    payload = _good_payload(request)
    payload["article"]["claim_evidence"] = [{
        "claim_text": "这里有一个自拟演示数字。",
        "claim_type": "calculation",
        "support_type": "synthetic_case",
        "support_refs": ["case_bundle"],
        "evidence_note": "self-authored demonstration",
    }]
    with pytest.raises(CreatorFirstError, match="case_label"):
        validate_creator_output(request, payload)


def test_human_style_blocks_internal_engineering_language():
    article = _good_payload(build_creator_request(request_id="test008"))["article"]
    article["content"] += "<p>这个 Draft Packet 的 angle_delivery 已完成。</p>"
    report = evaluate_creator_style(article)
    assert report.passed is False
    assert any("engineering language" in error for error in report.errors)
