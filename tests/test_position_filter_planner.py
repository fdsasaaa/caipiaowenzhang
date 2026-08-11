import json

from engine import planner


def _capability():
    return {
        "mechanics_verified": True,
        "economics_verified": False,
        "mechanics_rule_refs": ["M1"],
        "economics_rule_refs": [],
    }


def _setup(monkeypatch, tmp_path, rows):
    clusters = tmp_path / "clusters.jsonl"
    clusters.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    articles = tmp_path / "articles.jsonl"
    articles.write_text("", encoding="utf-8")
    monkeypatch.setattr(planner, "CLUSTERS", clusters)
    monkeypatch.setattr(planner, "ARTICLES", articles)
    monkeypatch.setattr(planner, "rule_capability", lambda provider, lottery, play: _capability())


def test_fixed_window_plan_uses_verified_play_selector_not_first_source_position(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path, [{
        "family_id": "F-SPAN",
        "source_count": 20,
        "risk_rate": 0.1,
        "lotteries": ["时时彩"],
        "positions": ["万位", "后三", "前四"],
        "technique_atoms": ["position_filter", "span_range"],
        "source_classifications": [],
        "example_source_ids": ["S1"],
        "article_generation_status": "eligible_after_rule_binding",
    }])
    result = planner.plan_articles("", "时时彩", "后三直选", 5)
    assert len(result["plans"]) == 1
    plan = result["plans"][0]
    assert plan["resolved_selector"] == "后三"
    assert plan["case_plan"]["resolved_selector"] == "后三"
    assert plan["case_plan"]["case_engine_ready"] is True
    assert [x["metric"] for x in plan["case_plan"]["supported"]] == ["selector", "span"]


def test_fixed_window_mismatch_is_not_emitted(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path, [{
        "family_id": "F-WRONG",
        "source_count": 50,
        "risk_rate": 0.0,
        "lotteries": ["时时彩"],
        "positions": ["万位", "前四"],
        "technique_atoms": ["position_filter", "span_range"],
        "source_classifications": [],
        "example_source_ids": ["S2"],
        "article_generation_status": "eligible_after_rule_binding",
    }])
    result = planner.plan_articles("", "时时彩", "后三直选", 5)
    assert result["plans"] == []


def test_located_family_expands_to_explicit_single_position_plans(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path, [{
        "family_id": "F-OMISSION",
        "source_count": 16,
        "risk_rate": 0.2,
        "lotteries": ["时时彩"],
        "positions": ["前四", "个位", "十位", "后三", "千位"],
        "technique_atoms": ["position_filter", "omission_threshold"],
        "source_classifications": ["定位胆"],
        "example_source_ids": ["S3"],
        "article_generation_status": "eligible_after_rule_binding",
    }])
    result = planner.plan_articles("", "时时彩", "定位胆", 10)
    assert [p["resolved_selector"] for p in result["plans"]] == ["千位", "十位", "个位"]
    assert all(p["case_plan"]["case_engine_ready"] for p in result["plans"])
    assert len({p["angle_signature"] for p in result["plans"]}) == 3


def test_located_frequency_without_source_position_uses_explicit_example_default(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path, [{
        "family_id": "F-HOT",
        "source_count": 11,
        "risk_rate": 0.2,
        "lotteries": ["时时彩"],
        "positions": [],
        "technique_atoms": ["cold_hot_split"],
        "source_classifications": ["定位胆"],
        "example_source_ids": ["S4"],
        "article_generation_status": "eligible_after_rule_binding",
    }])
    result = planner.plan_articles("", "时时彩", "定位胆", 5)
    plan = result["plans"][0]
    assert plan["resolved_selector"] == "个位"
    assert plan["selector_basis"] == "deterministic_example_default"
    assert plan["case_plan"]["source_position_supported"] is False
    assert plan["case_plan"]["case_engine_ready"] is True
