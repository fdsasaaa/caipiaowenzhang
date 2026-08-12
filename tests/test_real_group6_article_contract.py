from __future__ import annotations

from engine.real_group6_article_contract import (
    DOMAIN_BOUNDARY,
    FAMILY_ID,
    PRIMARY_KEYWORD,
    SOURCE_BOUNDARY,
    SOURCE_REF,
    build_real_group6_article_packet,
    build_real_group6_article_prompt,
    evaluate_real_group6_article,
)
from engine.real_knowledge_family_matrix import EXECUTABLE_ATOM_ORDER


def _good_article() -> dict:
    packet = build_real_group6_article_packet()
    content = (
        f"<p>{SOURCE_BOUNDARY}</p>"
        f"<p>{DOMAIN_BOUNDARY}</p>"
        "<h2>先看玩法结构</h2>"
        "<p>组六要求三个数字互不相同，投注单位按无序数字集合理解。例如{1,2,3}是一个组六投注单位，"
        "它对应6个有序排列：123、132、213、231、312、321。</p>"
        "<p>完整组六域共有120个无序投注单位，对应720个组六结构的有序开奖结果；"
        "全部三位有序结果空间是1000，所以720/1000=72%只是组六结构占全部三位结果的比例。</p>"
        "<p>如果把120个组六单位全部使用，则是120/120=100%的组六目标域覆盖，超过90%执行上限，"
        "因此这里仅解释完整玩法域，不提供全域投注。</p>"
        "<p>112有两个数字相同、一个不同，所以属于组三，不属于组六；777是三同号，既不是组六也不是组三。</p>"
        "<h2>实际怎么复算</h2>"
        "<ol><li>固定分分彩后三组六。</li><li>检查三个数字是否互不相同。</li>"
        "<li>把同一组三位数字的排列归到一个无序组六单位。</li><li>用123的六个排列核对覆盖关系。</li>"
        "<li>解释到玩法域和结构占比后停止；任何实际投注子集必须另开合同。</li></ol>"
    )
    return {
        "article_id": packet["article_id"],
        "title": "分分彩后三组六技巧：120个组选单位和720种排列怎么理解",
        "seo_title": "分分彩后三组六技巧：120个组选单位和720种排列怎么理解",
        "slug": "ffc-last3-group6-120-units-720-orders",
        "meta_description": "用分分彩后三组六案例解释120个无序组选单位、720个有序排列，以及72%结构占比和目标玩法覆盖率的区别。",
        "primary_keyword": PRIMARY_KEYWORD,
        "secondary_keywords": ["分分彩组六", "后三组六", "组六投注技巧", "组六号码结构"],
        "search_intent": "学习分分彩后三组六的投注单位、排列覆盖和来源边界",
        "summary": "解释组六无序投注单位与有序开奖结果的关系，并区分结构占比与目标玩法覆盖率。",
        "category": "投注技巧",
        "site_category_key": "tzjq",
        "content_type": "technique_article",
        "content_format": "html",
        "tags": ["分分彩", "后三组六", "组六结构"],
        "content": content,
        "rule_refs": packet["immutable_facts"]["rule_refs"],
        "source_refs": packet["immutable_facts"]["source_refs"],
        "case_scope": "mechanics_only",
        "status": "draft",
        "generation_contract_version": "2.0",
        "claim_evidence": [],
        "editorial_contract_version": "1.1",
        "practical_guidance": {
            "steps": [
                "固定分分彩后三组六。",
                "检查三个数字是否互不相同。",
                "将排列归到一个无序组六单位。",
                "用123的六种排列核对覆盖。",
                "解释完玩法域后停止。",
            ],
            "starting_space": "120个组六无序投注单位",
            "after_primary_filter_space": "不做投注过滤；本文解释完整玩法域",
            "parameter_freeze_rule": "组六为系统在看演示样本前预冻结的验证模式。",
            "stop_condition": "解释到组六玩法域和示例核对后停止；不输出全域投注。",
            "next_step_policy": "若要设计实际投注子集，必须另起合同，选择不超过90%的目标玩法域并重新通过金额/经济参数门禁。",
        },
    }


def test_blueprint_and_packet_lock_real_family_system_group6_binding():
    packet = build_real_group6_article_packet()
    contract = packet["real_group6_validation"]
    facts = packet["immutable_facts"]

    assert packet["article_id"] == "VAL-RK-GROUP6-FAM-F8EFC151-V1"
    assert facts["technique_family"] == FAMILY_ID
    assert facts["source_refs"] == [SOURCE_REF]
    assert facts["rule_refs"] == ["SSC-HIST-MECH-3STAR-GROUP6-V1"]
    assert facts["subject_lottery"] == "分分彩"
    assert facts["lottery"] == "时时彩"
    assert contract["binding"]["group_mode"] == "group6"
    assert contract["binding"]["source_did_not_choose_mode"] is True
    assert contract["group6_unit_count"] == 120
    assert contract["ordered_group6_outcome_count"] == 720
    assert contract["global_structure_share"] == 0.72
    assert contract["target_play_full_domain_coverage"] == 1.0
    assert contract["target_coverage_ceiling"] == 0.90
    assert contract["full_domain_executable_portfolio_allowed"] is False
    assert contract["normalized_bets_allowed"] is False
    assert "group3_group6" not in EXECUTABLE_ATOM_ORDER


def test_prompt_contains_exact_provenance_and_coverage_denominator_boundaries():
    prompt = build_real_group6_article_prompt()
    assert SOURCE_BOUNDARY in prompt
    assert DOMAIN_BOUNDARY in prompt
    assert "720/1000=72%" in prompt
    assert "120/120=100%" in prompt
    assert "不得把72%写成低于90%所以可全投" in prompt
    assert "读者显示层继续优先使用‘分分彩’" in prompt


def test_good_group6_article_passes_custom_quality_gate():
    report = evaluate_real_group6_article(_good_article())
    assert report.passed is True, report.errors
    assert report.score == 100


def test_source_recommendation_claim_is_rejected():
    article = _good_article()
    article["content"] += "<p>BRBCW-004115推荐组六。</p>"
    report = evaluate_real_group6_article(article)
    assert report.passed is False
    assert any("unsafe executable/source claim" in error for error in report.errors)


def test_wrong_72_percent_executable_inference_is_rejected():
    article = _good_article()
    article["content"] += "<p>72%低于90%所以可以全投。</p>"
    report = evaluate_real_group6_article(article)
    assert report.passed is False
    assert any("unsafe executable/source claim" in error for error in report.errors)


def test_normalized_bets_are_forbidden_in_domain_explanation_article():
    article = _good_article()
    article["normalized_bets"] = []
    report = evaluate_real_group6_article(article)
    assert report.passed is False
    assert any("normalized_bets" in error for error in report.errors)


def test_large_group6_unit_dump_is_rejected():
    article = _good_article()
    article["content"] += "<p>" + "、".join(str(i) for i in range(200)) + "</p>"
    report = evaluate_real_group6_article(article)
    assert report.passed is False
    assert any("dump" in error for error in report.errors)


def test_reader_facing_legacy_ssc_term_is_rejected_in_core_field():
    article = _good_article()
    article["title"] = "时时彩后三组六技巧：120个组选单位怎么理解"
    report = evaluate_real_group6_article(article)
    assert report.passed is False
    assert any("legacy 时时彩" in error for error in report.errors)
