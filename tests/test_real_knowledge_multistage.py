from __future__ import annotations

import pytest

from engine.article_memory import get_article_record
from engine.filter_pipeline import evaluate_filter_pipeline
from engine.knowledge_io import iter_brbcw_families
from engine.real_knowledge_multistage import (
    RealKnowledgePipelineError,
    build_real_knowledge_filter_pipeline,
    real_knowledge_pipeline_evidence,
)


REAL_ARTICLE_ID = "LCM-IDEA-bf5a9864b004ae17"
REAL_FAMILY_ID = "FAM-32137acbb90340b9"


def _real_family() -> dict:
    return next(row for row in iter_brbcw_families() if row["f"] == REAL_FAMILY_ID)


def test_real_source_family_is_present_in_static_archive_with_expected_provenance():
    family = _real_family()
    assert family["a"] == ["big_small_filter", "odd_even_filter"]
    assert family["n"] == 6
    assert family["e"] == ["BRBCW-003787"]


def test_existing_real_family_article_becomes_exact_two_stage_ordered_space():
    article = get_article_record(REAL_ARTICLE_ID)
    assert article is not None
    assert article["technique_family"] == REAL_FAMILY_ID
    assert article["rule_refs"] == ["SSC-HIST-MECH-LAST2-BSOE-V1"]

    spec = build_real_knowledge_filter_pipeline(article)
    result = evaluate_filter_pipeline(spec)

    assert spec["space_type"] == "ordered_2digit"
    assert spec["starting_space"] == 100
    assert [stage["atom"] for stage in spec["stages"]] == ["big_small_filter", "odd_even_filter"]
    assert [stage["after_space"] for stage in result["stages"]] == [50, 26]
    assert [stage["excluded_space"] for stage in result["stages"]] == [50, 24]
    assert result["final_space"] == 26
    assert spec["source_refs"] == ["BRBCW-003787"]
    assert spec["parameter_policy"] == "prefrozen_research_presets_v1_not_source_claim_not_predictive"


def test_real_family_evidence_keeps_all_write_and_publish_paths_off():
    article = get_article_record(REAL_ARTICLE_ID)
    evidence = real_knowledge_pipeline_evidence(article)
    assert evidence["registry_write"] is False
    assert evidence["website_write"] is False
    assert evidence["scheduled"] is False
    assert evidence["published"] is False
    assert "not source claims" in evidence["source_parameter_boundary"]


def test_sample_dependent_family_fails_closed_instead_of_inventing_parameters():
    article = get_article_record("LCM-IDEA-48eb8743fbbbad11")
    assert article is not None
    assert article["technique_atoms"] == ["cold_hot_split"]
    with pytest.raises(RealKnowledgePipelineError, match="cannot be converted"):
        build_real_knowledge_filter_pipeline(article)


def test_three_stage_research_preset_is_prefrozen_and_each_stage_reduces():
    record = {
        "technique_family": "FAM-TEST-THREE-STAGE",
        "play": "后三直选",
        "technique_atoms": ["sum_range", "span_range", "odd_even_filter"],
        "source_refs": ["BRBCW-TEST"],
        "source_support_count": 3,
        "source_risk_rate": 0.0,
    }
    spec = build_real_knowledge_filter_pipeline(record)
    result = evaluate_filter_pipeline(spec)
    assert spec["space_type"] == "ordered_3digit"
    assert [stage["after_space"] for stage in result["stages"]] == [760, 534, 210]
    assert result["stage_count"] == 3


def test_partial_conversion_is_not_allowed_when_family_has_unbound_atom():
    record = {
        "technique_family": "FAM-TEST-PARTIAL",
        "play": "后三直选",
        "technique_atoms": ["sum_range", "span_range", "cold_hot_split"],
        "source_refs": ["BRBCW-TEST"],
    }
    with pytest.raises(RealKnowledgePipelineError, match="cold_hot_split"):
        build_real_knowledge_filter_pipeline(record)
