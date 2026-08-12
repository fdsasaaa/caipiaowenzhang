from __future__ import annotations

import pytest

from engine.group_domain_contract import (
    GROUP3_RULE_REF,
    GROUP6_RULE_REF,
    GroupDomainContractError,
    classify_three_digit_structure,
    group3_bet_units,
    group6_bet_units,
    group_domain_summary,
    high_leverage_family_domain_diagnostic,
    require_group_mode,
)
from engine.real_knowledge_family_matrix import EXECUTABLE_ATOM_ORDER


def test_three_digit_structure_partition_is_exact():
    summary = group_domain_summary()
    assert summary["ordered_space"] == 1000
    assert summary["group3_ordered_outcomes"] == 270
    assert summary["group6_ordered_outcomes"] == 720
    assert summary["triple_same_ordered_outcomes"] == 10
    assert 270 + 720 + 10 == 1000


def test_unordered_bet_units_match_verified_ordered_coverage():
    summary = group_domain_summary()
    assert len(group3_bet_units()) == 90
    assert len(group6_bet_units()) == 120
    assert summary["group3_bet_units"] == 90
    assert summary["group6_bet_units"] == 120
    assert summary["group3_ordered_coverage"] == 270
    assert summary["group6_ordered_coverage"] == 720
    assert summary["rule_refs"] == [GROUP3_RULE_REF, GROUP6_RULE_REF]
    assert summary["domain_kind"] == "unordered_group_bet_units_with_ordered_outcome_coverage"


def test_structure_examples_are_not_conflated():
    assert classify_three_digit_structure("112") == "group3"
    assert classify_three_digit_structure("121") == "group3"
    assert classify_three_digit_structure("211") == "group3"
    assert classify_three_digit_structure("123") == "group6"
    assert classify_three_digit_structure("777") == "triple_same"
    with pytest.raises(GroupDomainContractError):
        classify_three_digit_structure("12")


def test_group_atom_requires_explicit_mode_binding():
    assert require_group_mode("组三") == "group3"
    assert require_group_mode("组选6") == "group6"
    with pytest.raises(GroupDomainContractError, match="group_mode"):
        require_group_mode(None)
    with pytest.raises(GroupDomainContractError, match="group_mode"):
        require_group_mode("group3_group6")


def test_high_leverage_archive_families_remain_fail_closed():
    report = high_leverage_family_domain_diagnostic()
    assert report["group_atom_executable"] is False
    assert report["dan_atom_executable"] is False
    assert report["current_filter_pipeline_whitelist_changed"] is False
    assert "group3_group6" not in EXECUTABLE_ATOM_ORDER
    assert "dan_candidate" not in EXECUTABLE_ATOM_ORDER

    group_rows = {row["family_id"]: row for row in report["group_families"]}
    dan_rows = {row["family_id"]: row for row in report["dan_families"]}

    assert "FAM-f8efc151837be787" in group_rows
    assert group_rows["FAM-f8efc151837be787"]["source_refs"] == ["BRBCW-004115"]
    assert group_rows["FAM-f8efc151837be787"]["family_executable"] is False
    assert group_rows["FAM-f8efc151837be787"]["required_parameter"] == "group_mode=group3|group6"

    assert "FAM-dbcf832f1ce7eedc" in dan_rows
    assert dan_rows["FAM-dbcf832f1ce7eedc"]["source_refs"] == ["BRBCW-000438"]
    assert dan_rows["FAM-dbcf832f1ce7eedc"]["family_executable"] is False
    assert "candidate_digit_set" in dan_rows["FAM-dbcf832f1ce7eedc"]["required_parameters"]


def test_public_display_name_does_not_rewrite_historical_rule_taxonomy():
    summary = group_domain_summary()
    assert summary["reader_lottery_label"] == "分分彩"
    assert summary["internal_rule_taxonomy"] == "时时彩"
    assert summary["provider_mapping_required"] is True
