from engine.technique_semantics import case_requirements


def test_supported_atoms_map_to_executable_metrics():
    result = case_requirements(["sum_range", "omission_threshold"])
    metrics = {row["atom"]: row["metric"] for row in result["supported"]}
    assert metrics["sum_range"] == "digit_sum"
    assert metrics["omission_threshold"] == "current_omission"
    assert result["unsupported"] == []
    assert result["case_engine_ready"] is True


def test_unsupported_atom_blocks_full_case_engine():
    result = case_requirements(["sum_range", "carry_mapping"])
    assert [row["atom"] for row in result["supported"]] == ["sum_range"]
    assert result["unsupported"] == ["carry_mapping"]
    assert result["case_engine_ready"] is False


def test_frequency_semantics_do_not_claim_prediction():
    result = case_requirements(["cold_hot_split"])
    spec = result["supported"][0]
    assert spec["metric"] == "frequency"
    assert "阈值" in spec["safe_article_use"]
