from __future__ import annotations

import pytest

from engine.real_knowledge_family_matrix import (
    MAX_SOURCE_RISK_RATE,
    MIN_SOURCE_SUPPORT,
    RealKnowledgeFamilyMatrixError,
    TARGET_ALREADY_ACCEPTED_FAMILY,
    build_real_knowledge_family_feasibility_report,
    build_real_knowledge_family_matrix_report,
    select_real_knowledge_family_matrix,
)


def test_feasibility_scan_reads_real_archive_and_preserves_strict_policy():
    report = build_real_knowledge_family_feasibility_report()
    assert report["funnel"]["total_families"] > 0
    assert report["strict_policy_unchanged"] is True
    assert report["selection_policy"]["min_source_support"] == MIN_SOURCE_SUPPORT
    assert report["selection_policy"]["max_source_risk_rate"] == MAX_SOURCE_RISK_RATE
    assert report["selection_policy"]["sample_dependent_atoms_allowed"] is False
    assert report["selection_policy"]["position_binding_is_source_play_claim"] is False
    assert report["paid_model_call"] is False
    assert report["registry_write"] is False
    assert report["website_write"] is False
    assert report["scheduled"] is False
    assert report["published"] is False


def test_strict_matrix_never_fabricates_candidates_when_archive_is_insufficient():
    report = build_real_knowledge_family_feasibility_report()
    strict_count = report["strict_eligible_count"]
    if strict_count < 3:
        with pytest.raises(RealKnowledgeFamilyMatrixError, match="fewer than three safely executable"):
            select_real_knowledge_family_matrix(limit=5)
    else:
        selected = select_real_knowledge_family_matrix(limit=5)
        assert 3 <= len(selected) <= 5
        assert len({item.family_id for item in selected}) == len(selected)
        assert len({item.signature for item in selected}) == len(selected)
        assert TARGET_ALREADY_ACCEPTED_FAMILY not in {item.family_id for item in selected}


def test_matrix_report_returns_diagnostic_instead_of_relaxing_zero_result():
    report = build_real_knowledge_family_matrix_report(limit=5)
    assert report["strict_eligible_count"] >= 0
    if report["strict_eligible_count"] < 3:
        assert report["status"] == "strict_single_family_matrix_not_feasible"
        assert report["selected_count"] == 0
        assert report["selected"] == []
        assert "independently source-backed single-atom families" in report["next_architecture_question"]
    else:
        assert report["status"] == "offline_matrix_selected"
        assert 3 <= report["selected_count"] <= 5


def test_nearest_rows_respect_source_gates_and_expose_composition_evidence_only():
    report = build_real_knowledge_family_feasibility_report()
    for row in report["nearest_bindable_single_atom_families"]:
        assert row["family_id"] != TARGET_ALREADY_ACCEPTED_FAMILY
        assert row["source_support_count"] >= MIN_SOURCE_SUPPORT
        assert row["source_risk_rate"] <= MAX_SOURCE_RISK_RATE
        assert row["source_ref"].startswith("BRBCW-")
        assert len(row["executable_atoms"]) == 1
        assert row["experimental_play"] in {"后二直选", "后三直选"}
        assert row["space_type"] in {"ordered_2digit", "ordered_3digit"}
        assert row["rule_ref"] in {"SSC-HIST-MECH-2STAR-LAST-V1", "SSC-HIST-MECH-3STAR-LAST-V1"}
        assert row["binding_basis"] == "archive_position_mask_experimental_binding_not_source_play_claim"

    for item in report["composition_ready_spaces"]:
        assert item["space_type"] in {"ordered_2digit", "ordered_3digit"}
        assert len(item["distinct_atoms"]) >= 2
