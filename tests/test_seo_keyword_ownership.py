from engine import approval, article_memory, seo_keywords


def test_method_primary_keywords_are_specific_to_the_actual_angle():
    assert seo_keywords.primary_keyword_for("分分彩", "后二大小单双", ["big_small_filter", "odd_even_filter"]) == "分分彩后二大小单双技巧"
    assert seo_keywords.primary_keyword_for("分分彩", "定位胆", ["cold_hot_split"]) == "分分彩定位胆冷热技巧"
    assert seo_keywords.primary_keyword_for("分分彩", "定位胆", ["omission_threshold", "position_filter"]) == "分分彩定位胆遗漏技巧"
    assert seo_keywords.primary_keyword_for("分分彩", "后三组选3", ["sum_range"]) == "分分彩后三组选3和值技巧"
    assert seo_keywords.primary_keyword_for("分分彩", "后三直选", ["position_filter", "span_range"]) == "分分彩后三直选跨度技巧"


def test_legacy_method_registry_rows_use_canonical_keyword_without_history_rewrite():
    legacy = {
        "primary_keyword": "分分彩定位胆技巧",
        "information_gain_type": "method_mechanics_and_reproducible_case",
        "subject_lottery": "分分彩",
        "subject_play": "定位胆",
        "technique_atoms": ["cold_hot_split"],
    }
    assert seo_keywords.canonical_primary_keyword(legacy) == "分分彩定位胆冷热技巧"


def test_current_registry_has_no_exact_primary_keyword_conflict_under_v13_policy():
    assert seo_keywords.keyword_ownership_conflicts() == []
    cold = seo_keywords.keyword_owners("分分彩定位胆冷热技巧")
    omission = seo_keywords.keyword_owners("分分彩定位胆遗漏技巧")
    assert [row["article_id"] for row in cold] == ["LCM-IDEA-48eb8743fbbbad11"]
    assert [row["article_id"] for row in omission] == ["LCM-IDEA-07838cdf108296a7"]
    assert seo_keywords.keyword_owners("分分彩定位胆技巧") == []


def test_reserve_rechecks_keyword_owner_even_for_ready_blueprint(monkeypatch):
    monkeypatch.setattr(
        article_memory,
        "keyword_owners",
        lambda keyword, exclude_article_id=None: [{"article_id": "LCM-OWNER", "status": "approved"}],
    )
    bp = {
        "article_id": "LCM-NEW",
        "blueprint_id": "BP-NEW",
        "status": "ready_for_draft",
        "site_category_key": "tzjq",
        "content_type": "technique_article",
        "primary_keyword": "分分彩定位胆冷热技巧",
    }
    result = article_memory.reserve_blueprints([bp])
    assert result["reserved_count"] == 0
    assert result["skipped"][0]["reason"] == "primary_keyword_owned"
    assert result["skipped"][0]["owner"] == "LCM-OWNER"


def test_approval_contract_rejects_keyword_owned_by_another_article(monkeypatch):
    monkeypatch.setattr(
        approval,
        "keyword_owners",
        lambda keyword, exclude_article_id=None: [{"article_id": "LCM-OWNER", "status": "approved"}],
    )
    packet = {
        "article_id": "LCM-NEW",
        "seo": {
            "primary_keyword": "分分彩定位胆冷热技巧",
            "search_intent": "学习具体投注技巧并看懂可复算案例",
        },
    }
    article = {
        "article_id": "LCM-NEW",
        "title": "分分彩定位胆冷热技巧：测试标题",
        "slug": "test-slug",
        "meta_description": "测试描述",
        "primary_keyword": "分分彩定位胆冷热技巧",
        "search_intent": "学习具体投注技巧并看懂可复算案例",
    }
    errors, _ = approval._seo_contract(packet, article)
    assert "exact primary_keyword already owned by active article: LCM-OWNER" in errors


def test_conflict_audit_reports_two_active_owners(monkeypatch):
    rows = [
        {"article_id": "A", "status": "approved", "primary_keyword": "同一关键词"},
        {"article_id": "B", "status": "idea", "primary_keyword": "同一 关键词"},
        {"article_id": "C", "status": "rejected_for_revision", "primary_keyword": "同一关键词"},
    ]
    monkeypatch.setattr(seo_keywords, "iter_registry", lambda kind: iter(rows))
    conflicts = seo_keywords.keyword_ownership_conflicts()
    assert conflicts == [{"primary_keyword": "同一关键词", "article_ids": ["A", "B"]}]
