from __future__ import annotations

import pytest

from engine.production_filter_contract import (
    ProductionFilterContractError,
    build_primary_filter_spec,
    build_production_filter_contract,
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
        "source_refs": ["SOURCE-1"],
    }


def test_five_digit_span_contract_is_exact_and_reducing():
    spec = build_primary_filter_spec(_bp("五星直选", ["position_filter", "span_range"], "五星"), {})
    assert spec["candidate_space_type"] == "ordered_5digit"
    assert spec["params"] == {"min": 2, "max": 6}
    assert spec["starting_space"] == 100000
    assert spec["after_filter_space"] == 43620
    assert spec["excluded_space"] == 56380
    assert spec["basis"] == "experimental_parameter"
    assert spec["selection_rule_freeze_before_observation"] is True
    assert spec["resolved_parameters_derived_from_synthetic_case"] is False
    assert spec["parameter_freeze_before_observation"] is True
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


def test_multi_method_article_must_execute_all_methods_in_order():
    contract = build_production_filter_contract(
        _bp("后三直选", ["position_filter", "sum_range", "span_range"], "后三"),
        {},
    )
    assert contract["mode"] == "multistage"
    assert contract["method_atoms"] == ["sum_range", "span_range"]
    assert set(contract["method_atoms_covered"]) == {"sum_range", "span_range"}
    result = contract["filter_pipeline_result"]
    assert result["starting_space"] == 1000
    assert result["stage_count"] == 2
    assert [(row["before_space"], row["after_space"], row["excluded_space"]) for row in result["stages"]] == [
        (1000, 670, 330),
        (670, 396, 274),
    ]
    assert result["final_space"] == 396
    assert result["total_excluded"] == 604

    with pytest.raises(ProductionFilterContractError, match="multistage"):
        build_primary_filter_spec(
            _bp("后三直选", ["position_filter", "sum_range", "span_range"], "后三"),
            {},
        )


def test_noop_later_method_blocks_instead_of_silently_ignoring_it():
    # Every group3 unit already has a repeated digit. After the sum stage,
    # repeat_number is still a no-op and therefore the A+B article must block.
    with pytest.raises(ProductionFilterContractError, match="does not make a strict reduction"):
        build_production_filter_contract(
            _bp("后三组选3", ["repeat_number", "sum_range"], "后三"),
            {},
        )


def test_frequency_contract_distinguishes_frozen_rule_from_sample_derived_digits():
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
    assert spec["selection_rule_freeze_before_observation"] is True
    assert spec["resolved_parameters_derived_from_synthetic_case"] is True
    assert spec["parameter_freeze_before_observation"] is False


def test_cold_hot_and_frequency_window_are_one_compound_stage_not_duplicate_noop_filters():
    case_bundle = {
        "selector": "后三",
        "frequency": {
            "sample_size": 12,
            "top_frequency_digits": [7, 2, 5],
        },
    }
    contract = build_production_filter_contract(
        _bp("后三直选", ["cold_hot_split", "frequency_window"], "后三"),
        case_bundle,
    )
    assert contract["mode"] == "single_stage"
    stage = contract["filter_pipeline_result"]["stages"][0]
    assert stage["atom"] == "cold_hot_frequency_window"
    assert stage["covered_atoms"] == ["cold_hot_split", "frequency_window"]
    assert stage["before_space"] == 1000
    assert stage["after_space"] == 27
    assert stage["support_mode"] == "synthetic_case_calculation"
    assert stage["selection_rule_freeze_before_observation"] is True
    assert stage["resolved_parameters_derived_from_synthetic_case"] is True
    assert stage["parameter_freeze_before_observation"] is False
    assert set(contract["method_atoms_covered"]) == {"cold_hot_split", "frequency_window"}


def test_static_plus_sample_stage_preserves_each_stage_provenance():
    case_bundle = {
        "selector": "后三",
        "frequency": {
            "sample_size": 12,
            "top_frequency_digits": [7, 2, 5],
        },
    }
    contract = build_production_filter_contract(
        _bp("后三直选", ["sum_range", "frequency_window"], "后三"),
        case_bundle,
    )
    result = contract["filter_pipeline_result"]
    assert result["stage_count"] == 2
    assert result["stages"][0]["support_mode"] == "verified_rule_calculation"
    assert result["stages"][1]["support_mode"] == "synthetic_case_calculation"
    assert (result["stages"][0]["before_space"], result["stages"][0]["after_space"]) == (1000, 670)
    assert (result["stages"][1]["before_space"], result["stages"][1]["after_space"]) == (670, 22)


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
    assert spec["selection_rule_freeze_before_observation"] is True
    assert spec["resolved_parameters_derived_from_synthetic_case"] is True
    assert spec["parameter_freeze_before_observation"] is False


def test_unsupported_reader_method_atom_blocks_whole_article():
    with pytest.raises(ProductionFilterContractError, match="unsupported method atoms"):
        build_production_filter_contract(_bp("后三直选", ["sum_range", "dan_candidate"], "后三"), {})


def test_daxiaodanshuang_numeric_contract_fails_closed():
    with pytest.raises(ProductionFilterContractError):
        build_primary_filter_spec(_bp("后二大小单双", ["big_small_filter"], "后二"), {})
