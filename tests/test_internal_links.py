from engine import internal_links


def test_current_linkable_articles_plan_without_fake_urls():
    result = internal_links.plan_all_internal_links(limit=3)
    expected_ids = {str(row["article_id"]) for row in internal_links._linkable_records()}
    actual_ids = {str(plan["article_id"]) for plan in result["plans"]}
    assert result["article_count"] == len(expected_ids)
    assert len(result["plans"]) == len(expected_ids)
    assert actual_ids == expected_ids
    assert result["resolved_targets"] == 0
    assert result["pending_targets"] > 0
    for plan in result["plans"]:
        assert internal_links.audit_internal_link_plan(plan) == []
        for target in plan["targets"]:
            assert target["resolution_status"] == "pending_published_url"
            assert target["url"] is None
            assert target["target_article_id"] != plan["article_id"]


def test_dingweidan_cold_hot_prefers_omission_and_format_guide(monkeypatch):
    rows = [
        {
            "article_id": "SOURCE",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "定位胆",
            "content_type": "technique_article",
            "primary_keyword": "分分彩定位胆冷热技巧",
            "technique_atoms": ["cold_hot_split"],
        },
        {
            "article_id": "A-OMISSION",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "定位胆",
            "content_type": "technique_article",
            "primary_keyword": "分分彩定位胆遗漏技巧",
            "technique_atoms": ["omission_threshold", "position_filter"],
        },
        {
            "article_id": "B-FORMAT",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "定位胆",
            "content_type": "technique_article",
            "primary_keyword": "分分彩定位胆格式教程",
            "technique_atoms": ["format_mechanics"],
        },
        {
            "article_id": "C-WEAK",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "五星直选",
            "content_type": "technique_article",
            "primary_keyword": "分分彩五星直选教程",
            "technique_atoms": [],
        },
    ]
    monkeypatch.setattr(internal_links, "iter_registry", lambda kind: iter(rows))
    plan = internal_links.plan_internal_links("SOURCE", limit=3)
    ids = [target["target_article_id"] for target in plan["targets"]]
    assert ids[:2] == ["A-OMISSION", "B-FORMAT"]
    anchors = {target["target_article_id"]: target["anchor_hint"] for target in plan["targets"]}
    assert anchors["A-OMISSION"] == "分分彩定位胆遗漏技巧"


def test_last3_sum_connects_to_last3_span_before_broader_three_digit_content(monkeypatch):
    rows = [
        {
            "article_id": "SOURCE",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "后三组选3",
            "content_type": "technique_article",
            "primary_keyword": "分分彩后三组选3和值技巧",
            "technique_atoms": ["sum_range"],
        },
        {
            "article_id": "LCM-IDEA-62bfa71c95642c9d",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "后三直选",
            "content_type": "technique_article",
            "primary_keyword": "分分彩后三直选跨度技巧",
            "technique_atoms": ["position_filter", "span_range"],
        },
        {
            "article_id": "LCM-ANGLE-11c1d01b80765af0",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "中三组选3",
            "content_type": "technique_article",
            "primary_keyword": "分分彩中三组选3和值注数计算",
            "technique_atoms": ["sum_range"],
        },
    ]
    monkeypatch.setattr(internal_links, "iter_registry", lambda kind: iter(rows))
    plan = internal_links.plan_internal_links("SOURCE", limit=3)
    assert plan["targets"][0]["target_article_id"] == "LCM-IDEA-62bfa71c95642c9d"
    assert plan["targets"][0]["score"] >= 60
    assert "shared_play_group:三星,后三" in plan["targets"][0]["reasons"]
    assert plan["targets"][0]["anchor_hint"] == "分分彩后三直选跨度技巧"
    assert plan["targets"][0]["score"] > plan["targets"][1]["score"]


def test_no_forced_link_when_only_same_lottery_is_available(monkeypatch):
    rows = [
        {
            "article_id": "SOURCE",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "后二大小单双",
            "content_type": "technique_article",
            "primary_keyword": "分分彩后二大小单双技巧",
            "technique_atoms": ["big_small_filter", "odd_even_filter"],
        },
        {
            "article_id": "SAME-LOTTERY-ONLY",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "五星直选",
            "content_type": "technique_article",
            "primary_keyword": "分分彩五星直选教程",
            "technique_atoms": ["span_range"],
        },
    ]
    monkeypatch.setattr(internal_links, "iter_registry", lambda kind: iter(rows))
    plan = internal_links.plan_internal_links("SOURCE", limit=3)
    assert plan["status"] == "planned"
    assert plan["targets"] == []


def test_published_target_resolves_url_but_unpublished_target_does_not(monkeypatch):
    rows = [
        {
            "article_id": "SOURCE",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "定位胆",
            "content_type": "technique_article",
            "primary_keyword": "源技巧",
            "technique_atoms": ["cold_hot_split"],
        },
        {
            "article_id": "PUBLISHED",
            "status": "published",
            "subject_lottery": "分分彩",
            "subject_play": "定位胆",
            "content_type": "technique_article",
            "primary_keyword": "已发布技巧",
            "technique_atoms": ["omission_threshold"],
            "published_url": "https://www.laocaimi.org/published-example",
        },
        {
            "article_id": "APPROVED",
            "status": "approved",
            "subject_lottery": "分分彩",
            "subject_play": "定位胆",
            "content_type": "technique_article",
            "primary_keyword": "待发布技巧",
            "technique_atoms": ["position_filter"],
            "published_url": None,
        },
    ]
    monkeypatch.setattr(internal_links, "iter_registry", lambda kind: iter(rows))
    plan = internal_links.plan_internal_links("SOURCE", limit=3)
    by_id = {target["target_article_id"]: target for target in plan["targets"]}
    assert by_id["PUBLISHED"]["resolution_status"] == "resolved"
    assert by_id["PUBLISHED"]["url"] == "https://www.laocaimi.org/published-example"
    assert by_id["APPROVED"]["resolution_status"] == "pending_published_url"
    assert by_id["APPROVED"]["url"] is None


def test_audit_rejects_self_duplicate_and_fake_pending_url():
    plan = {
        "article_id": "A",
        "min_score": 45,
        "targets": [
            {"target_article_id": "A", "score": 50, "resolution_status": "pending_published_url", "url": None},
            {"target_article_id": "B", "score": 40, "resolution_status": "pending_published_url", "url": "https://fake"},
            {"target_article_id": "B", "score": 50, "resolution_status": "resolved", "url": None},
        ],
    }
    errors = internal_links.audit_internal_link_plan(plan)
    assert "self link is prohibited" in errors
    assert "duplicate target_article_id: B" in errors
    assert "pending target must not carry url: B" in errors
    assert "target below semantic threshold: B" in errors
    assert "resolved target missing url: B" in errors
