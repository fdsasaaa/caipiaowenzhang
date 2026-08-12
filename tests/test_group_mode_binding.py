from __future__ import annotations

import pytest

from engine.group_mode_binding import (
    SOURCE_BINDING,
    SYSTEM_BINDING,
    GroupModeBindingError,
    bind_group_mode,
)
from engine.real_knowledge_family_matrix import EXECUTABLE_ATOM_ORDER

GROUP_ONLY_FAMILY = "FAM-f8efc151837be787"
NON_GROUP_FAMILY = "FAM-c7549b61f340ef66"


def test_system_research_can_bind_group6_without_attributing_mode_to_source():
    binding = bind_group_mode(
        GROUP_ONLY_FAMILY,
        group_mode="组六",
        binding_basis=SYSTEM_BINDING,
    )
    assert binding["group_mode"] == "group6"
    assert binding["candidate_unit_count"] == 120
    assert binding["ordered_structure_size_within_all_three_digit_outcomes"] == 720
    assert binding["global_three_digit_structure_share"] == 0.72
    assert binding["target_play_unit_space"] == 120
    assert binding["target_play_domain_coverage_if_all_units_used"] == 1.0
    assert binding["target_coverage_ceiling_for_executable_portfolio"] == 0.90
    assert binding["all_domain_units_executable_portfolio_allowed"] is False
    assert binding["family_source_refs"] == ["BRBCW-004115"]
    assert binding["source_did_not_choose_mode"] is True
    assert binding["mode_provenance"]["owner"] == "system_research"
    assert "not a source recommendation" in binding["mode_provenance"]["claim_boundary"]
    assert binding["validation_only"] is True
    assert binding["production_eligible"] is False


def test_system_research_group3_separates_global_share_from_target_coverage():
    binding = bind_group_mode(
        GROUP_ONLY_FAMILY,
        group_mode="group3",
        binding_basis=SYSTEM_BINDING,
    )
    assert binding["candidate_unit_count"] == 90
    assert binding["ordered_structure_size_within_all_three_digit_outcomes"] == 270
    assert binding["global_three_digit_structure_share"] == 0.27
    assert binding["target_play_domain_coverage_if_all_units_used"] == 1.0
    assert binding["all_domain_units_executable_portfolio_allowed"] is False
    assert binding["candidate_unit_domain"] == "unordered_group_bet_units"


def test_global_structure_share_cannot_be_used_as_executable_coverage_denominator():
    binding = bind_group_mode(
        GROUP_ONLY_FAMILY,
        group_mode="组六",
        binding_basis=SYSTEM_BINDING,
    )
    assert "coverage_rate" not in binding
    assert "global_three_digit_structure_share is descriptive only" in binding["coverage_denominator_note"]
    assert binding["global_three_digit_structure_share"] < 0.90
    assert binding["target_play_domain_coverage_if_all_units_used"] > 0.90


def test_source_binding_fails_until_exact_source_article_is_materialized():
    with pytest.raises(GroupModeBindingError, match="materialized source article"):
        bind_group_mode(
            GROUP_ONLY_FAMILY,
            group_mode="组六",
            binding_basis=SOURCE_BINDING,
            source_ref="BRBCW-004115",
        )


def test_binding_never_guesses_from_compact_family_atom():
    with pytest.raises(GroupModeBindingError, match="group_mode"):
        bind_group_mode(
            GROUP_ONLY_FAMILY,
            group_mode="group3_group6",
            binding_basis=SYSTEM_BINDING,
        )


def test_binding_requires_prefreeze():
    with pytest.raises(GroupModeBindingError, match="frozen"):
        bind_group_mode(
            GROUP_ONLY_FAMILY,
            group_mode="组六",
            binding_basis=SYSTEM_BINDING,
            frozen_before_observation=False,
        )


def test_non_group_family_cannot_receive_group_binding():
    with pytest.raises(GroupModeBindingError, match="does not contain"):
        bind_group_mode(
            NON_GROUP_FAMILY,
            group_mode="组六",
            binding_basis=SYSTEM_BINDING,
        )


def test_parameter_binding_does_not_enable_group_atom_globally():
    assert "group3_group6" not in EXECUTABLE_ATOM_ORDER
    binding = bind_group_mode(
        GROUP_ONLY_FAMILY,
        group_mode="组六",
        binding_basis=SYSTEM_BINDING,
    )
    assert binding["registry_write"] is False
    assert binding["website_write"] is False
    assert binding["scheduled"] is False
    assert binding["published"] is False
    assert binding["paid_model_call"] is False
