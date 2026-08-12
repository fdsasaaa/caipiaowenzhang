from __future__ import annotations

from engine.claim_evidence import _hard_sentences
from engine.quality import _public_terminology_review, _verified_mechanics_from_explicit_refs
from engine.real_knowledge_composite_article_contract import build_composite_article_packet
from engine.real_knowledge_composite_evidence import normalize_composite_claim_metadata


def test_negative_safety_sentence_is_not_a_hard_performance_claim():
    safe = "这套文章不负责把筛选结果包装成命中率、胜率或推荐号码。"
    assert _hard_sentences(safe) == []


def test_positive_performance_tail_is_still_blocked():
    unsafe = "这套文章不负责把筛选结果包装成命中率，但是实际命中率更高。"
    assert _hard_sentences(unsafe) == [unsafe.rstrip("。")]


def test_explicit_verified_rule_ref_can_bridge_internal_taxonomy_and_ffc_display_name():
    article = {
        "lottery": "分分彩",
        "subject_lottery": "分分彩",
        "play": "后三直选",
        "rule_refs": ["SSC-HIST-MECH-3STAR-LAST-V1"],
    }
    assert _verified_mechanics_from_explicit_refs(article) == ["SSC-HIST-MECH-3STAR-LAST-V1"]


def test_ffc_reader_facing_core_fields_reject_legacy_ssc_term():
    article = {
        "subject_lottery": "分分彩",
        "title": "时时彩后三技巧",
        "seo_title": "分分彩后三技巧",
        "meta_description": "分分彩案例",
        "primary_keyword": "分分彩后三技巧",
        "content": "<p>分分彩案例。</p>",
    }
    errors, warnings, penalty = _public_terminology_review(article)
    assert errors
    assert "title" in errors[0]
    assert penalty == 20
    assert warnings == []


def test_ffc_content_allows_small_historical_internal_reference_but_warns_unqualified_usage():
    qualified = {
        "subject_lottery": "分分彩",
        "title": "分分彩后三技巧",
        "seo_title": "分分彩后三技巧",
        "meta_description": "分分彩案例",
        "primary_keyword": "分分彩后三技巧",
        "content": "<p>历史规则库内部仍把 时时彩 作为 mechanics 分类名，正文玩法统一称分分彩。</p>",
    }
    errors, warnings, penalty = _public_terminology_review(qualified)
    assert errors == []
    assert warnings == []
    assert penalty == 0

    unqualified = dict(qualified)
    unqualified["content"] = "<p>时时彩后三可以按和值做筛选。</p>"
    errors, warnings, penalty = _public_terminology_review(unqualified)
    assert errors == []
    assert warnings
    assert penalty == 5


def test_composite_stop_metadata_normalizes_only_when_two_stage_semantics_are_already_explicit():
    packet = build_composite_article_packet()
    article = {
        "content": "<p>正文不得改变。</p>",
        "claim_evidence": [],
        "practical_guidance": {
            "steps": ["第一层和值。", "第二层跨度后停止。"],
            "stop_condition": "完成和值层和跨度层后停止；新增条件另开实验。",
            "next_step_policy": "否则在第二层结束，不追加第三层。",
        },
    }
    normalized = normalize_composite_claim_metadata(packet, article)
    assert normalized["content"] == article["content"]
    assert article["practical_guidance"]["stop_condition"] == "完成和值层和跨度层后停止；新增条件另开实验。"
    assert "第二层" in normalized["practical_guidance"]["stop_condition"]
