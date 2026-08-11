from engine import planner


def _cluster_json():
    return '{"cluster_id":"C1","family_id":"F1","source_count":5,"risk_rate":0.1,"lotteries":["时时彩"],"positions":["个位"],"technique_atoms":["omission_threshold"],"source_classifications":["定位胆"],"example_source_ids":["S1"],"article_generation_status":"eligible_after_rule_binding"}\n'


def _setup(monkeypatch, tmp_path, capability):
    cluster = tmp_path / "clusters.jsonl"
    cluster.write_text(_cluster_json(), encoding="utf-8")
    articles = tmp_path / "articles.jsonl"
    articles.write_text("", encoding="utf-8")
    monkeypatch.setattr(planner, "CLUSTERS", cluster)
    monkeypatch.setattr(planner, "ARTICLES", articles)
    monkeypatch.setattr(planner, "rule_capability", lambda provider, lottery, play: capability)


def test_planner_blocks_without_verified_mechanics(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path, {
        "mechanics_verified": False, "economics_verified": False,
        "mechanics_rule_refs": [], "economics_rule_refs": []
    })
    result = planner.plan_articles("provider-a", "时时彩", "定位胆", 3)
    assert result["status"] == "blocked_mechanics_verification"
    assert result["plans"][0]["allowed_case_scope"] == "idea_only"


def test_planner_allows_mechanics_only_without_economics(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path, {
        "mechanics_verified": True, "economics_verified": False,
        "mechanics_rule_refs": ["M1"], "economics_rule_refs": []
    })
    result = planner.plan_articles("provider-a", "时时彩", "定位胆", 3)
    assert result["status"] == "ready_mechanics_only"
    assert result["plans"][0]["rule_refs"] == ["M1"]
    assert result["plans"][0]["allowed_case_scope"] == "mechanics_only"


def test_planner_allows_full_case_with_economics(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path, {
        "mechanics_verified": True, "economics_verified": True,
        "mechanics_rule_refs": ["M1"], "economics_rule_refs": ["E1"]
    })
    result = planner.plan_articles("provider-a", "时时彩", "定位胆", 3)
    assert result["status"] == "ready_full"
    assert result["plans"][0]["allowed_case_scope"] == "economics"


def test_planner_filters_unrelated_play_and_deduplicates_angles(monkeypatch, tmp_path):
    cluster = tmp_path / "clusters.jsonl"
    cluster.write_text(
        _cluster_json() +
        '{"cluster_id":"C2","family_id":"F1","source_count":3,"risk_rate":0.1,"lotteries":["时时彩"],"positions":["个位"],"technique_atoms":["omission_threshold"],"source_classifications":["定位胆"],"example_source_ids":["S2"],"article_generation_status":"eligible_after_rule_binding"}\n' +
        '{"cluster_id":"C3","family_id":"F3","source_count":99,"risk_rate":0.0,"lotteries":["时时彩"],"positions":[],"technique_atoms":["group3_group6"],"source_classifications":["组选"],"example_source_ids":["S3"],"article_generation_status":"eligible_after_rule_binding"}\n',
        encoding="utf-8")
    articles = tmp_path / "articles.jsonl"
    articles.write_text("", encoding="utf-8")
    monkeypatch.setattr(planner, "CLUSTERS", cluster)
    monkeypatch.setattr(planner, "ARTICLES", articles)
    monkeypatch.setattr(planner, "rule_capability", lambda provider, lottery, play: {
        "mechanics_verified": False, "economics_verified": False,
        "mechanics_rule_refs": [], "economics_rule_refs": []
    })
    result = planner.plan_articles("provider-a", "时时彩", "定位胆", 10)
    assert len(result["plans"]) == 1
    assert result["plans"][0]["technique_family"] == "F1"


def test_compact_family_archive_is_available():
    rows = list(planner.iter_brbcw_families())
    assert len(rows) == 759
