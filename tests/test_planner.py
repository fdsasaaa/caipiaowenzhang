from engine import planner


def _cluster_json():
    return '{"cluster_id":"C1","family_id":"F1","source_count":5,"risk_rate":0.1,"lotteries":["时时彩"],"positions":["个位"],"technique_atoms":["omission_threshold"],"source_classifications":["定位胆"],"example_source_ids":["S1"],"article_generation_status":"eligible_after_rule_binding"}\n'


def test_planner_blocks_without_verified_rule(monkeypatch, tmp_path):
    cluster = tmp_path / "clusters.jsonl"
    cluster.write_text(_cluster_json(), encoding="utf-8")
    articles = tmp_path / "articles.jsonl"
    articles.write_text('', encoding='utf-8')
    monkeypatch.setattr(planner, "CLUSTERS", cluster)
    monkeypatch.setattr(planner, "ARTICLES", articles)
    monkeypatch.setattr(planner, "verified_rules", lambda provider, lottery, play: [])
    result = planner.plan_articles("provider-a", "时时彩", "定位胆", 3)
    assert result["status"] == "blocked_rule_verification"
    assert result["plans"][0]["status"] == "blocked_rule_verification"


def test_planner_allows_with_verified_rule(monkeypatch, tmp_path):
    cluster = tmp_path / "clusters.jsonl"
    cluster.write_text(_cluster_json(), encoding="utf-8")
    articles = tmp_path / "articles.jsonl"
    articles.write_text('', encoding='utf-8')
    monkeypatch.setattr(planner, "CLUSTERS", cluster)
    monkeypatch.setattr(planner, "ARTICLES", articles)
    monkeypatch.setattr(planner, "verified_rules", lambda provider, lottery, play: [{"rule_id":"R1"}])
    result = planner.plan_articles("provider-a", "时时彩", "定位胆", 3)
    assert result["status"] == "ready"
    assert result["plans"][0]["rule_refs"] == ["R1"]


def test_planner_filters_unrelated_play_and_deduplicates_angles(monkeypatch, tmp_path):
    cluster = tmp_path / "clusters.jsonl"
    cluster.write_text(
        _cluster_json() +
        '{"cluster_id":"C2","family_id":"F1","source_count":3,"risk_rate":0.1,"lotteries":["时时彩"],"positions":["个位"],"technique_atoms":["omission_threshold"],"source_classifications":["定位胆"],"example_source_ids":["S2"],"article_generation_status":"eligible_after_rule_binding"}\n' +
        '{"cluster_id":"C3","family_id":"F3","source_count":99,"risk_rate":0.0,"lotteries":["时时彩"],"positions":[],"technique_atoms":["group3_group6"],"source_classifications":["组选"],"example_source_ids":["S3"],"article_generation_status":"eligible_after_rule_binding"}\n',
        encoding="utf-8")
    articles = tmp_path / "articles.jsonl"
    articles.write_text('', encoding='utf-8')
    monkeypatch.setattr(planner, "CLUSTERS", cluster)
    monkeypatch.setattr(planner, "ARTICLES", articles)
    monkeypatch.setattr(planner, "verified_rules", lambda provider, lottery, play: [])
    result = planner.plan_articles("provider-a", "时时彩", "定位胆", 10)
    assert len(result["plans"]) == 1
    assert result["plans"][0]["technique_family"] == "F1"


def test_compact_family_archive_is_available():
    rows = list(planner.iter_brbcw_families())
    assert len(rows) == 759
