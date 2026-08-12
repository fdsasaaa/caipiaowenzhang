from __future__ import annotations

from copy import deepcopy

from engine.real_knowledge_composite_article_contract import (
    ARTICLE_ID,
    CANDIDATE_INTEGRITY_BOUNDARY,
    ORDER_BOUNDARY,
    PRIMARY_KEYWORD,
    SOURCE_BOUNDARY,
    build_composite_article_blueprint,
    build_composite_article_packet,
    build_composite_article_prompt,
    evaluate_composite_article_content,
)
from engine.real_knowledge_composition import EXPECTED_CANDIDATE_SHA256


def _digits(value: str) -> list[int]:
    return [int(ch) for ch in value]


def _sum_span(value: str) -> tuple[int, int]:
    digits = _digits(value)
    return sum(digits), max(digits) - min(digits)


def test_blueprint_preserves_two_source_boundaries_and_unregistered_validation_identity():
    blueprint = build_composite_article_blueprint()
    contract = blueprint["composition_contract"]
    assert blueprint["article_id"] == ARTICLE_ID
    assert blueprint["primary_keyword"] == PRIMARY_KEYWORD
    assert blueprint["article_status"] == "validation_only_unregistered_identity"
    assert blueprint["rule_refs"] == ["SSC-HIST-MECH-3STAR-LAST-V1"]
    assert blueprint["source_refs"] == ["BRBCW-006020", "BRBCW-002590"]
    assert blueprint["technique_atoms"] == ["sum_range", "span_range"]
    assert contract["composition_basis"] == "system_authored_cross_family_composition_not_source_claim"
    assert contract["binding_basis"] == "archive_position_mask_experimental_binding_not_source_play_claim"
    assert contract["parameter_policy"] == "prefrozen_research_presets_v1_not_source_claim_not_predictive"
    assert contract["final_candidate_count"] == 534
    assert contract["final_candidate_sha256"] == EXPECTED_CANDIDATE_SHA256
    assert contract["must_list_all_final_candidates"] is False
    assert contract["must_explain_how_to_test_any_candidate"] is True


def test_packet_exposes_exact_machine_path_but_does_not_require_534_number_dump():
    packet = build_composite_article_packet()
    result = packet["practicality"]["filter_pipeline_result"]
    assert result["starting_space"] == 1000
    assert [stage["after_space"] for stage in result["stages"]] == [760, 534]
    assert [stage["excluded_space"] for stage in result["stages"]] == [240, 226]
    assert result["final_space"] == 534
    assert result["total_excluded"] == 466
    assert packet["practicality"]["minimum_concrete_steps"] == 6
    assert packet["real_knowledge_composition"]["must_list_all_final_candidates"] is False


def test_spot_checks_are_deterministic_and_represent_both_pass_and_fail_cases():
    contract = build_composite_article_packet()["real_knowledge_composition"]
    included = contract["spot_checks"]["included"]
    excluded = contract["spot_checks"]["excluded"]
    assert len(included) == 6
    assert len(excluded) == 6
    assert len(set(included)) == 6
    assert len(set(excluded)) == 6
    assert set(included).isdisjoint(excluded)

    for value in included:
        total, span = _sum_span(value)
        assert 8 <= total <= 19
        assert 3 <= span <= 7

    for value in excluded:
        total, span = _sum_span(value)
        assert not (8 <= total <= 19 and 3 <= span <= 7)


def test_prompt_forbids_false_source_composition_and_requires_reader_facing_reproduction():
    prompt = build_composite_article_prompt()
    assert SOURCE_BOUNDARY in prompt
    assert ORDER_BOUNDARY in prompt
    assert CANDIDATE_INTEGRITY_BOUNDARY in prompt
    assert "1000" in prompt and "760" in prompt and "534" in prompt
    assert "240" in prompt and "226" in prompt and "466" in prompt
    assert "不要求把534个候选全部塞进正文" in prompt
    assert "不得写‘来源推荐和值+跨度组合’" in prompt
    assert "和值=sum(三位数字)" in prompt
    assert "跨度=max-min" in prompt
    assert "第二层完成后停止" in prompt


def _good_article() -> dict:
    contract = build_composite_article_packet()["real_knowledge_composition"]
    included = contract["spot_checks"]["included"]
    excluded = contract["spot_checks"]["excluded"]
    content = (
        f"<p>{SOURCE_BOUNDARY}</p>"
        f"<p>{ORDER_BOUNDARY}</p>"
        "<p>后三直选从000到999一共1000个有序结果。第一层和值8–19：1000筛到760，排除240。"
        "第二层跨度3–7：760筛到534，再排除226；整体总排除466。</p>"
        "<p>手工检查任意号码时，先算和值=sum(三位数字)，再算跨度=最大值减最小值；"
        "先通过和值8–19，再通过跨度3–7，才属于最终534个集合。</p>"
        f"<p>{CANDIDATE_INTEGRITY_BOUNDARY}</p>"
        f"<p>入选核对示例：{'、'.join(included)}；排除核对示例：{'、'.join(excluded)}。</p>"
        f"<p>例如{included[0]}的和值与跨度都满足两层条件；{included[1]}同样按同一公式复算。"
        f"而{excluded[0]}或{excluded[1]}至少有一层不满足，所以被排除。</p>"
        "<p>演示数据，不是真实开奖记录。这里的空间收缩不代表预测优势、命中率或盈利能力。</p>"
    )
    return {
        "content": content,
        "practical_guidance": {
            "steps": [
                "固定后三直选000–999空间",
                "先算和值",
                "按8–19完成第一层",
                "再算跨度=最大减最小",
                "按3–7完成第二层",
                "用固定示例复算并停止",
            ],
            "stop_condition": "第二层完成后停止，不临时追加第三层。",
        },
    }


def test_quality_gate_rewards_explanation_not_full_candidate_dump():
    article = _good_article()
    report = evaluate_composite_article_content(article)
    assert report.passed is True
    assert report.score == 100


def test_quality_gate_fails_when_source_boundaries_are_blurred():
    article = _good_article()
    article["content"] = article["content"].replace(SOURCE_BOUNDARY, "来源推荐和值+跨度组合，并规定先和值后跨度。")
    report = evaluate_composite_article_content(article)
    assert report.passed is False
    assert any("required composite provenance" in error for error in report.errors)
    assert "composition/order/parameters were falsely attributed to sources" in report.errors


def test_quality_gate_fails_if_machine_path_is_missing_even_when_prose_sounds_reasonable():
    article = _good_article()
    article["content"] = article["content"].replace("1000筛到760，排除240", "第一层会缩小一部分号码")
    report = evaluate_composite_article_content(article)
    assert report.passed is False
    assert any("760" in error or "240" in error for error in report.errors)


def test_quality_gate_rejects_giant_candidate_dump_as_substitute_for_explanation():
    article = _good_article()
    article = deepcopy(article)
    article["content"] += "<p>" + "、".join(f"{i:03d}" for i in range(250)) + "</p>"
    report = evaluate_composite_article_content(article)
    assert report.passed is False
    assert "content appears to dump a large candidate list instead of explaining the method" in report.errors
