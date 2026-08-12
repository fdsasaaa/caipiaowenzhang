from __future__ import annotations

from copy import deepcopy

from engine.real_knowledge_ai_generation import build_real_knowledge_generation_prompt
from engine.real_knowledge_live_validation import (
    SOURCE_PARAMETER_BOUNDARY,
    TARGET_ARTICLE_ID,
    build_real_knowledge_live_blueprint,
    build_real_knowledge_live_packet,
    evaluate_real_knowledge_article,
    normalize_real_knowledge_article,
)


EXPECTED_CANDIDATES = [
    "05", "07", "09", "16", "18", "25", "27", "29", "36", "38", "45", "47", "49",
    "50", "52", "54", "61", "63", "70", "72", "74", "81", "83", "90", "92", "94",
]


def test_real_live_blueprint_reuses_existing_identity_but_upgrades_information_gain():
    blueprint = build_real_knowledge_live_blueprint()
    assert blueprint["article_id"] == TARGET_ARTICLE_ID
    assert blueprint["primary_keyword"] == "分分彩后二大小单双技巧"
    assert blueprint["technique_family"] == "FAM-32137acbb90340b9"
    assert blueprint["technique_atoms"] == ["big_small_filter", "odd_even_filter"]
    assert blueprint["source_refs"] == ["BRBCW-003787"]
    assert blueprint["source_support_count"] == 6
    assert blueprint["rule_refs"] == ["SSC-HIST-MECH-LAST2-BSOE-V1"]
    assert blueprint["status"] == "ready_for_draft"
    assert blueprint["article_status"] == "validation_only_existing_identity"
    assert blueprint["information_gain_type"] == "source_backed_prefrozen_multistage_candidate_enumeration"


def test_real_live_packet_is_exactly_100_to_50_to_26_and_lists_all_values():
    packet = build_real_knowledge_live_packet()
    result = packet["practicality"]["filter_pipeline_result"]
    assert result["starting_space"] == 100
    assert [stage["after_space"] for stage in result["stages"]] == [50, 26]
    assert [stage["excluded_space"] for stage in result["stages"]] == [50, 24]
    assert result["final_space"] == 26
    assert result["total_excluded"] == 74

    contract = packet["real_knowledge_validation"]
    assert contract["final_candidates"] == EXPECTED_CANDIDATES
    assert contract["required_final_candidate_line"] == (
        "最终26个二位候选值：" + "、".join(EXPECTED_CANDIDATES) + "。"
    )
    assert contract["required_source_parameter_boundary"] == SOURCE_PARAMETER_BOUNDARY
    assert contract["registry_write"] is False
    assert contract["website_write"] is False
    assert contract["scheduled"] is False
    assert contract["published"] is False


def test_real_knowledge_prompt_requires_provenance_boundary_and_concrete_candidates():
    packet = build_real_knowledge_live_packet()
    prompt = build_real_knowledge_generation_prompt(packet)
    assert SOURCE_PARAMETER_BOUNDARY in prompt
    assert packet["real_knowledge_validation"]["required_final_candidate_line"] in prompt
    assert "不能只给数量" in prompt
    assert "不是推荐号码、命中率、胜率或下一期预测" in prompt
    assert "来源证明一大一小更好" in prompt
    assert "演示数据，不是真实开奖记录。" in prompt


def _quality_candidate_article(packet: dict) -> dict:
    contract = packet["real_knowledge_validation"]
    content = (
        "<h2>先说清来源和参数边界</h2>"
        f"<p>{contract['required_source_parameter_boundary']}</p>"
        "<h2>两层怎么复算</h2>"
        "<p>后二十位和个位有顺序，所以00–99一共100个有序结果。</p>"
        "<p>第一层固定一大一小：100个筛到50个，排除50个。</p>"
        "<p>第二层固定一单一双：50个筛到26个，排除24个。</p>"
        "<p>两层完成后最终26个，整体总排除74个；这只是候选空间数学，不代表预测优势。</p>"
        f"<p>{contract['required_final_candidate_line']}</p>"
        "<p>演示数据，不是真实开奖记录。</p>"
    )
    return {
        "content": content,
        "claim_evidence": [],
        "practical_guidance": {
            "steps": [
                "固定后二十位和个位",
                "写出0–4小、5–9大",
                "按一大一小完成第一层",
                "按一单一双完成第二层",
                "核对26个候选值并停止",
            ],
            "starting_space": "100个有序后二结果",
            "after_primary_filter_space": "26个最终候选",
            "parameter_freeze_rule": "所有参数在演示样本前冻结",
            "stop_condition": "第二层完成后停止",
            "next_step_policy": "新增条件必须下一次实验前绑定规则或证据并冻结",
        },
    }


def test_real_knowledge_quality_gate_passes_only_with_full_candidate_explanation():
    packet = build_real_knowledge_live_packet()
    article = _quality_candidate_article(packet)
    report = evaluate_real_knowledge_article(packet, article)
    assert report.passed is True
    assert report.score == 100


def test_real_knowledge_quality_gate_fails_if_model_only_gives_counts():
    packet = build_real_knowledge_live_packet()
    article = _quality_candidate_article(packet)
    candidate_line = packet["real_knowledge_validation"]["required_final_candidate_line"]
    article["content"] = article["content"].replace(f"<p>{candidate_line}</p>", "")
    report = evaluate_real_knowledge_article(packet, article)
    assert report.passed is False
    assert "complete final 26-candidate line missing or changed" in report.errors


def test_real_knowledge_quality_gate_fails_if_source_parameter_boundary_is_blurred():
    packet = build_real_knowledge_live_packet()
    article = _quality_candidate_article(packet)
    article["content"] = article["content"].replace(
        SOURCE_PARAMETER_BOUNDARY,
        "来源告诉我们一大一小和一单一双更好。",
    )
    report = evaluate_real_knowledge_article(packet, article)
    assert report.passed is False
    assert "source/parameter provenance boundary sentence missing or changed" in report.errors


def test_real_knowledge_normalizer_adds_evidence_but_never_repairs_missing_content():
    packet = build_real_knowledge_live_packet()
    article = _quality_candidate_article(packet)
    normalized = normalize_real_knowledge_article(packet, article)
    rows = {row["claim_text"]: row for row in normalized["claim_evidence"]}
    assert rows[SOURCE_PARAMETER_BOUNDARY]["support_type"] == "source_unverified"
    assert rows[SOURCE_PARAMETER_BOUNDARY]["support_refs"] == ["BRBCW-003787"]
    candidate_line = packet["real_knowledge_validation"]["required_final_candidate_line"]
    assert rows[candidate_line]["support_type"] == "verified_rule"
    assert rows[candidate_line]["support_refs"] == ["SSC-HIST-MECH-LAST2-BSOE-V1"]

    broken = deepcopy(article)
    broken["content"] = broken["content"].replace(candidate_line, "")
    normalized_broken = normalize_real_knowledge_article(packet, broken)
    assert candidate_line not in normalized_broken["content"]
    assert evaluate_real_knowledge_article(packet, normalized_broken).passed is False
