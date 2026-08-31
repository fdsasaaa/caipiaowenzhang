from __future__ import annotations

from engine.title_seo import (
    TITLE_CLICKABILITY_CHECK,
    TITLE_DUPLICATION_CHECK,
    TITLE_KEYWORD_DIVERSITY,
    TITLE_NUMERIC_CLAIM_VERIFIED,
    TITLE_SEARCH_INTENT_CHECK,
    TITLE_TOPIC_MATCH,
    TITLE_SEO_CONTRACT_VERSION,
    audit_public_release_titles,
    evaluate_title_seo,
)
from engine.title_seo_runtime import apply_title_seo


def _article(title: str) -> dict:
    return {
        "article_id": "TITLE-NEW-001",
        "title": title,
        "seo_title": title,
        "primary_keyword": "分分彩后三直选和值筛选步骤",
        "search_intent": "复核后三直选和值筛选的候选空间、输入输出与停止条件",
        "summary": "说明后三直选和值筛选如何复核，并区分组合计算与预测结论。",
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "play": "后三直选",
        "technique_atoms": ["sum_range"],
        "information_gain_type": "execution_checklist",
        "content": (
            "<h2>候选空间怎么复核</h2>"
            "<p>本文讨论后三直选和值筛选的输入、输出和停止条件。</p>"
            "<p>候选空间的缩小只说明约束增加，不能单独证明未来预测优势。</p>"
        ),
        "claim_evidence": [],
        "title_seo_contract_version": TITLE_SEO_CONTRACT_VERSION,
        "title_selection_reason": "test",
        "title_candidates": [
            title,
            "从输入到结果：后三直选和值筛选的空间变化与停止边界",
            "和值筛选到底在算什么？从后三直选的输入到结果",
            "和值筛选为什么容易误读？用后三直选看组合计算边界",
            "先看候选空间，再谈和值筛选：哪些结论不能直接推出",
        ],
    }


def test_natural_title_can_pass_without_fenfen_or_exact_primary_keyword() -> None:
    title = "做到哪一步应该停？后三直选和值筛选的复核清单"
    article = _article(title)
    review = evaluate_title_seo(article, comparison_records=[])
    assert review.passed is True
    assert "分分彩" not in title
    assert article["primary_keyword"] not in title
    assert all(result.passed for result in review.gates.values())


def test_generic_fenfen_template_prefix_is_blocked() -> None:
    article = _article("分分彩技巧：后三直选和值筛选方法")
    article["title_candidates"] = [
        "分分彩技巧：后三直选和值筛选方法",
        "分分彩方法：后三直选和值筛选",
        "分分彩教程：后三直选和值筛选",
    ]
    review = evaluate_title_seo(article, comparison_records=[])
    assert review.passed is False
    assert review.gates[TITLE_KEYWORD_DIVERSITY].passed is False
    assert review.gates[TITLE_CLICKABILITY_CHECK].passed is False


def test_candidate_set_requires_structural_and_prefix_diversity() -> None:
    article = _article("分分彩后三直选和值：怎么复核候选空间")
    article["title_candidates"] = [
        "分分彩后三直选和值：怎么复核候选空间",
        "分分彩后三直选和值：为什么要看停止条件",
        "分分彩后三直选和值：如何检查输入输出",
    ]
    review = evaluate_title_seo(article, comparison_records=[])
    gate = review.gates[TITLE_KEYWORD_DIVERSITY]
    assert gate.passed is False
    assert any("must not start" in reason or "distinct title structures" in reason for reason in gate.reasons)


def test_numeric_title_claim_must_exist_in_body_or_evidence() -> None:
    article = _article("200期复盘后，后三直选和值筛选暴露了什么问题？")
    article["title_candidates"][0] = article["title"]
    review = evaluate_title_seo(article, comparison_records=[])
    assert review.gates[TITLE_NUMERIC_CLAIM_VERIFIED].passed is False
    assert "200期" in review.gates[TITLE_NUMERIC_CLAIM_VERIFIED].details["unsupported"]

    article["content"] += "<p>这里把200期设为历史复盘窗口，只用于检查执行一致性。</p>"
    review = evaluate_title_seo(article, comparison_records=[])
    assert review.gates[TITLE_NUMERIC_CLAIM_VERIFIED].passed is True


def test_near_duplicate_title_is_blocked() -> None:
    article = _article("做到哪一步应该停？后三直选和值筛选的复核清单")
    existing = [{
        "article_id": "OLD-001",
        "title": "做到哪一步应该停？后三直选和值筛选复核清单",
    }]
    review = evaluate_title_seo(article, comparison_records=existing)
    assert review.gates[TITLE_DUPLICATION_CHECK].passed is False
    assert review.gates[TITLE_DUPLICATION_CHECK].details["article_id"] == "OLD-001"


def test_topic_and_search_intent_cannot_be_replaced_by_unrelated_clickbait() -> None:
    article = _article("为什么很多人都看错了这个神秘规律？")
    article["title_candidates"][0] = article["title"]
    review = evaluate_title_seo(article, comparison_records=[])
    assert review.gates[TITLE_TOPIC_MATCH].passed is False
    assert review.gates[TITLE_SEARCH_INTENT_CHECK].passed is False


def test_apply_title_seo_generates_three_to_five_post_body_candidates() -> None:
    article = _article("分分彩后三直选和值筛选步骤：实际操作按哪几步做")
    article.pop("title_candidates")
    article.pop("title_seo_contract_version")
    article.pop("title_selection_reason")
    review = apply_title_seo(article, comparison_records=[])
    assert 3 <= len(article["title_candidates"]) <= 5
    assert len(set(article["title_candidates"])) == len(article["title_candidates"])
    assert article["title"] in article["title_candidates"]
    assert article["title"] == article["seo_title"]
    assert article["title_seo_contract_version"] == TITLE_SEO_CONTRACT_VERSION
    assert review.passed is True


def test_main_formal_public_release_inventory_audit_is_read_only_and_complete() -> None:
    report = audit_public_release_titles()
    assert report["formal_public_release_count"] == 68
    assert report["articles_modified"] is False
    assert report["website_side_effects"] is False
    assert len(report["rows"]) == 68
    assert all(len(row["suggested_title_1"]) > 0 for row in report["rows"])
    assert all("path" in row for row in report["rows"])
