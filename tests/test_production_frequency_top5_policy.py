from __future__ import annotations

from engine.production_filter_contract import (
    PRODUCTION_FREQUENCY_TOP_N,
    build_production_filter_contract,
)


def _blueprint(atoms: list[str]) -> dict:
    return {
        "article_id": "TOP5-TEST",
        "play": "后三直选",
        "subject_play": "后三直选",
        "resolved_selector": "后三",
        "technique_atoms": atoms,
        "rule_refs": ["SSC-HIST-MECH-3STAR-LAST-V1"],
        "source_refs": ["BRBCW-TEST"],
    }


def _case_bundle() -> dict:
    return {
        "selector": "后三",
        "frequency": {
            "sample_size": 12,
            "frequency": {
                0: 1,
                1: 5,
                2: 5,
                3: 4,
                4: 0,
                5: 3,
                6: 2,
                7: 5,
                8: 1,
                9: 0,
            },
            # Historical helper output may still carry Top-3. Production must
            # ignore this narrower resolved list when the complete frequency
            # table is available and apply its own fixed Top-5 rule.
            "top_frequency_digits": [1, 2, 7],
        },
    }


def test_full_frequency_table_uses_fixed_top5_not_historical_top3():
    contract = build_production_filter_contract(
        _blueprint(["frequency_window"]),
        _case_bundle(),
    )
    stage = contract["filter_pipeline_result"]["stages"][0]
    assert PRODUCTION_FREQUENCY_TOP_N == 5
    assert stage["params"]["top_n"] == 5
    assert stage["params"]["digits"] == [1, 2, 3, 5, 7]
    assert stage["params"]["ranking"] == "frequency_desc_then_digit_asc"
    assert stage["params"]["ranking_source"] == "full_frequency_table_top5"
    assert stage["params"]["production_top_n_policy"] == 5
    assert stage["before_space"] == 1000
    assert stage["after_space"] == 125
    assert stage["excluded_space"] == 875
    assert stage["selection_rule"]["top_n"] == 5
    assert stage["selection_rule_freeze_before_observation"] is True
    assert stage["resolved_parameters_derived_from_synthetic_case"] is True
    assert stage["parameter_freeze_before_observation"] is False
    assert stage["support_mode"] == "synthetic_case_calculation"
    assert stage["support_refs"] == ["case_bundle"]
    assert stage["source_recommendation_claimed"] is False
    assert stage["predictive_advantage_claimed"] is False


def test_compound_cold_hot_frequency_uses_one_top5_stage_covering_both_atoms():
    contract = build_production_filter_contract(
        _blueprint(["cold_hot_split", "frequency_window"]),
        _case_bundle(),
    )
    assert contract["mode"] == "single_stage"
    stage = contract["filter_pipeline_result"]["stages"][0]
    assert stage["atom"] == "cold_hot_frequency_window"
    assert stage["covered_atoms"] == ["cold_hot_split", "frequency_window"]
    assert stage["params"]["top_n"] == 5
    assert set(contract["method_atoms_covered"]) == {"cold_hot_split", "frequency_window"}
