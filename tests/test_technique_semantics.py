from engine.technique_semantics import case_requirements, fixed_selector_for_play, selector_variants


def test_supported_atoms_map_to_executable_metrics_with_selector():
    result = case_requirements(["sum_range"], "后三", "verified_play")
    metrics = {row["atom"]: row["metric"] for row in result["supported"]}
    assert metrics["sum_range"] == "digit_sum"
    assert result["unsupported"] == []
    assert result["resolved_selector"] == "后三"
    assert result["case_engine_ready"] is True


def test_omission_requires_single_position_selector():
    good = case_requirements(["omission_threshold"], "个位", "source_position")
    assert good["case_engine_ready"] is True
    bad = case_requirements(["omission_threshold"], "后三", "verified_play")
    assert bad["case_engine_ready"] is False
    assert bad["unsupported"] == ["omission_threshold:selector_not_supported:后三"]


def test_unsupported_atom_blocks_full_case_engine():
    result = case_requirements(["sum_range", "carry_mapping"], "后三", "verified_play")
    assert [row["atom"] for row in result["supported"]] == ["sum_range"]
    assert result["unsupported"] == ["carry_mapping"]
    assert result["case_engine_ready"] is False


def test_frequency_semantics_do_not_claim_prediction():
    result = case_requirements(["cold_hot_split"], "个位", "deterministic_example_default")
    spec = result["supported"][0]
    assert spec["metric"] == "frequency"
    assert "阈值" in spec["safe_article_use"]
    assert "下一期" in spec["safe_article_use"]


def test_position_filter_is_selector_binding_not_prediction_metric():
    result = case_requirements(["position_filter", "span_range"], "后三", "verified_play")
    assert result["case_engine_ready"] is True
    assert result["supported"][0]["metric"] == "selector"
    assert result["supported"][1]["metric"] == "span"
    assert "本身不是预测信号" in __import__('engine.technique_semantics', fromlist=['load_semantics']).load_semantics()["principle"]


def test_fixed_play_selector_wins_over_source_position_order():
    assert fixed_selector_for_play("后三直选") == "后三"
    variants = selector_variants("后三直选", ["万位", "后三", "前四"], ["position_filter", "span_range"])
    assert variants == [{"selector": "后三", "basis": "verified_play", "source_position_supported": True}]


def test_position_filter_rejects_family_that_does_not_support_target_window():
    assert selector_variants("后三直选", ["万位", "前四"], ["position_filter", "span_range"]) == []


def test_located_position_filter_expands_only_source_supported_single_positions():
    variants = selector_variants(
        "定位胆",
        ["前四", "个位", "十位", "后三", "千位"],
        ["position_filter", "omission_threshold"],
    )
    assert [x["selector"] for x in variants] == ["千位", "十位", "个位"]
    assert all(x["basis"] == "source_position" for x in variants)
