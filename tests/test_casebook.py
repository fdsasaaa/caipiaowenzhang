from engine.casebook import descriptive_case, frequency_case, omission_case

DRAWS = ["12345", "22346", "92347", "02348"]


def test_descriptive_case_contains_no_predictive_claim():
    case = descriptive_case(DRAWS, "后三")
    assert case["sample_size"] == 4
    assert case["latest_draw"] == "02348"
    assert case["claim_scope"] == "descriptive_only"
    assert case["predictive_guarantee"] is False
    assert len(case["sum_series"]) == 4


def test_omission_case_uses_explicit_threshold():
    case = omission_case(DRAWS, "个位", threshold=2)
    assert 5 in case["candidates_meeting_threshold"]
    assert 6 in case["candidates_meeting_threshold"]
    assert 7 not in case["candidates_meeting_threshold"]
    assert "不意味着" in case["method_note"]


def test_frequency_case_ranks_but_does_not_predict():
    case = frequency_case(DRAWS, "后二", lookback=4, hot_top_n=2)
    assert case["top_frequency_digits"][0] == 4
    assert "不代表未来" in case["method_note"]
