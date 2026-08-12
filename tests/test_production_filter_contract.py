from __future__ import annotations

import pytest

from engine.production_filter_contract import (
    ProductionFilterContractError,
    build_primary_filter_spec,
)


def _bp(play: str, atoms: list[str], selector: str | None = None) -> dict:
    return {
        "article_id": "T-1",
        "play": play,
        "subject_play": play,
        "resolved_selector": selector or (
            "五星" if "五星" in play else
            "后三" if "后三" in play else
            "后二" if "后二" in play else
            "个位"
        ),
        "technique_atoms": atoms,
        "rule_refs": ["RULE-1"],
    }


def test_five_digit_span_contract_is_exact_and_reducing():
    spec = build_primary_filter_spec(_bp("五星直选", ["position_filter", "span_range"], "五星"), {})
    assert spec["candidate_space_type"] == "ordered_5digit"
    assert spec["params"] == {"min": 2, "max": 6}
    assert spec["starting_space"] == 100000
    assert spec["after_filter_space"] == 43620
    assert spec["excluded_space"] == 56380
    assert spec["basis"] == "system_research_preset_not_source_claim"
    assert spec["predictive_advantage_claimed"] is False


def test_two_digit_sum_contract_is_exact():
    spec = build_primary_filter_spec(_bp("后二直选", ["sum_range"], "后二"), {})
    assert spec["starting_space"] == 100
    assert spec["after_filter_space"] == 58
    assert spec["excluded_space"] == 42
    assert spec["params"] == {"min": 6, "max": 12}


def test_two_digit_group_neighbor_contract_uses_45_group_space():
    spec = build_primary_filter_spec(_bp("后二组选", ["neighbor_number"], "后二"), {})
    assert spec["candidate_space_type"] == "unordered_2digit"
    assert spec["starting_space"] == 45
    assert spec["after_filter_space"] == 9
    assert spec["params"]["circular_0_9"] is False


def test_invalid_repeat_primary_falls_through_to_next_atom():
    # Group3 is already all repeated; repeat_number alone cannot reduce it.
    spec = build_primary_filter_spec(_bp("后三组选3", ["repeat_number", "sum_range"], "后三"), {})
    assert spec["atom"] == "sum_range"
    assert spec["starting_space"] == 90
    assert 0 < spec["after_filter_space"] < 90


def test_frequency_contract_uses_precomputed_fixed_top3_pool():
    case_bundle = {
        "selector": "后三",
        "frequency": {
            "sample_size": 12,
            "top_frequency_digits": [7, 2, 5],
        },
    }
    spec = build_primary_filter_spec(_bp("后三直选", ["frequency_window"], "后三"), case_bundle)
    assert spec["atom"] == "frequency_window"
    assert spec["params"] == {"lookback": 12, "top_n": 3, "digits": [2, 5, 7]}
    assert spec["starting_space"] == 1000
    assert spec["after_filter_space"] == 27
    assert spec["support_mode"] == "synthetic_case_calculation"


def test_omission_contract_requires_fixed_position_and_reduces_ten_digits():
    case_bundle = {
        "selector": "个位",
        "omission": {
            "sample_size": 12,
            "threshold": 2,
            "candidates_meeting_threshold": [0, 1, 3, 4, 5, 6, 8, 9],
        },
    }
    spec = build_primary_filter_spec(_bp("定位胆", ["omission_threshold"], "个位"), case_bundle)
    assert spec["starting_space"] == 10
    assert spec["after_filter_space"] == 8
    assert spec["excluded_space"] == 2
    assert spec["params"]["threshold"] == 2


def test_daxiaodanshuang_numeric_contract_fails_closed():
    with pytest.raises(ProductionFilterContractError):
        build_primary_filter_spec(_bp("后二大小单双", ["big_small_filter"], "后二"), {})
