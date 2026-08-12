from __future__ import annotations

from copy import deepcopy

import pytest

from engine.filter_pipeline import evaluate_filter_pipeline, final_pipeline_candidate_strings
from engine.real_knowledge_composition import (
    BINDING_BASIS,
    COMPOSITION_BASIS,
    EXPECTED_CANDIDATE_SHA256,
    EXPECTED_FINAL_SPACE,
    EXPECTED_STAGE_AFTER,
    EXPECTED_STAGE_EXCLUDED,
    EXPECTED_TOTAL_EXCLUDED,
    PARAMETER_POLICY,
    PLAY,
    RULE_REF,
    SPAN_FAMILY,
    SUM_FAMILY,
    build_sum_span_composite_evidence,
    build_sum_span_composite_pipeline,
)


def test_two_sources_remain_separate_and_neither_claims_the_composition():
    evidence = build_sum_span_composite_evidence()
    assert evidence["source_families"] == [SUM_FAMILY, SPAN_FAMILY]
    assert SUM_FAMILY["family_id"] != SPAN_FAMILY["family_id"]
    assert SUM_FAMILY["source_ref"] != SPAN_FAMILY["source_ref"]
    assert SUM_FAMILY["executable_atom"] == "sum_range"
    assert SPAN_FAMILY["executable_atom"] == "span_range"
    assert evidence["composition_basis"] == COMPOSITION_BASIS
    assert evidence["binding_basis"] == BINDING_BASIS
    assert evidence["parameter_policy"] == PARAMETER_POLICY
    assert "system-authored" in evidence["source_boundary"]
    assert "not source claims" in evidence["source_boundary"]
    assert "not evidence of predictive advantage" in evidence["source_boundary"]


def test_sum_span_pipeline_is_exactly_reproducible_on_verified_last3_space():
    spec = build_sum_span_composite_pipeline()
    result = evaluate_filter_pipeline(spec)
    assert spec["play"] == PLAY == "后三直选"
    assert spec["rule_ref"] == RULE_REF == "SSC-HIST-MECH-3STAR-LAST-V1"
    assert spec["space_type"] == "ordered_3digit"
    assert result["starting_space"] == 1000
    assert [stage["after_space"] for stage in result["stages"]] == EXPECTED_STAGE_AFTER == [760, 534]
    assert [stage["excluded_space"] for stage in result["stages"]] == EXPECTED_STAGE_EXCLUDED == [240, 226]
    assert result["final_space"] == EXPECTED_FINAL_SPACE == 534
    assert result["total_excluded"] == EXPECTED_TOTAL_EXCLUDED == 466


def test_each_stage_carries_only_its_own_source_family_and_system_parameter_provenance():
    spec = build_sum_span_composite_pipeline()
    stages = spec["stages"]
    assert stages[0]["atom"] == "sum_range"
    assert stages[0]["source_family"] == SUM_FAMILY["family_id"]
    assert stages[0]["support_ref"] == SUM_FAMILY["source_ref"]
    assert stages[0]["params"] == {"min": 8, "max": 19}

    assert stages[1]["atom"] == "span_range"
    assert stages[1]["source_family"] == SPAN_FAMILY["family_id"]
    assert stages[1]["support_ref"] == SPAN_FAMILY["source_ref"]
    assert stages[1]["params"] == {"min": 3, "max": 7}

    for stage in stages:
        assert stage["parameter_provenance"] == "system_research_preset_not_source_claim"
        assert stage["composition_order_provenance"] == "system_research_order_not_source_claim"


def test_final_candidate_enumeration_is_locked_by_count_and_hash():
    evidence = build_sum_span_composite_evidence()
    candidates = final_pipeline_candidate_strings(evidence["pipeline_spec"])
    assert len(candidates) == 534
    assert evidence["final_candidate_count"] == 534
    assert evidence["final_candidate_sha256"] == EXPECTED_CANDIDATE_SHA256
    assert evidence["final_candidate_preview_first"] == candidates[:20]
    assert evidence["final_candidate_preview_last"] == candidates[-20:]


def test_evidence_keeps_all_paid_write_and_publish_paths_off():
    evidence = build_sum_span_composite_evidence()
    assert evidence["paid_model_call"] is False
    assert evidence["registry_write"] is False
    assert evidence["website_write"] is False
    assert evidence["scheduled"] is False
    assert evidence["published"] is False


def test_changing_a_prefrozen_parameter_breaks_the_locked_evidence_contract():
    spec = build_sum_span_composite_pipeline()
    tampered = deepcopy(spec)
    tampered["stages"][0]["params"] = {"min": 9, "max": 19}
    result = evaluate_filter_pipeline(tampered)
    assert [stage["after_space"] for stage in result["stages"]] != EXPECTED_STAGE_AFTER


def test_reversing_system_authored_stage_order_is_detectable_even_if_final_set_matches():
    spec = build_sum_span_composite_pipeline()
    reversed_spec = deepcopy(spec)
    reversed_spec["stages"] = list(reversed(reversed_spec["stages"]))
    result = evaluate_filter_pipeline(reversed_spec)
    assert [stage["after_space"] for stage in result["stages"]] == [690, 534]
    assert result["final_space"] == 534
    assert [stage["after_space"] for stage in result["stages"]] != EXPECTED_STAGE_AFTER
