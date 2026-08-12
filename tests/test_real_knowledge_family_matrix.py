from __future__ import annotations

from engine.real_knowledge_family_matrix import (
    MAX_SOURCE_RISK_RATE,
    MIN_SOURCE_SUPPORT,
    TARGET_ALREADY_ACCEPTED_FAMILY,
    build_real_knowledge_family_matrix_report,
    select_real_knowledge_family_matrix,
)


def test_matrix_selects_three_to_five_distinct_source_backed_families():
    selected = select_real_knowledge_family_matrix(limit=5)
    assert 3 <= len(selected) <= 5
    assert len({item.family_id for item in selected}) == len(selected)
    assert len({item.signature for item in selected}) == len(selected)
    assert TARGET_ALREADY_ACCEPTED_FAMILY not in {item.family_id for item in selected}


def test_selected_matrix_is_fail_closed_and_machine_reproducible():
    selected = select_real_knowledge_family_matrix(limit=5)
    for item in selected:
        assert item.stage_count in {2, 3}
        assert item.source_support_count >= MIN_SOURCE_SUPPORT
        assert item.source_risk_rate <= MAX_SOURCE_RISK_RATE
        assert item.source_ref.startswith("BRBCW-")
        assert item.play in {"后二直选", "后三直选"}
        assert item.space_type in {"ordered_2digit", "ordered_3digit"}
        assert item.rule_ref in {"SSC-HIST-MECH-2STAR-LAST-V1", "SSC-HIST-MECH-3STAR-LAST-V1"}
        assert item.binding_basis == "archive_position_mask_experimental_binding_not_source_play_claim"
        assert len(item.final_candidates) == item.pipeline_result["final_space"]
        assert item.pipeline_result["final_space"] < item.pipeline_result["starting_space"]
        previous = item.pipeline_result["starting_space"]
        for stage in item.pipeline_result["stages"]:
            assert stage["before_space"] == previous
            assert stage["after_space"] < stage["before_space"]
            previous = stage["after_space"]


def test_report_keeps_all_paid_write_and_publish_paths_off():
    report = build_real_knowledge_family_matrix_report(limit=5)
    assert report["status"] == "offline_matrix_selected"
    assert report["eligible_count"] >= report["selected_count"] >= 3
    assert report["paid_model_call"] is False
    assert report["registry_write"] is False
    assert report["website_write"] is False
    assert report["scheduled"] is False
    assert report["published"] is False
    assert report["selection_policy"]["sample_dependent_atoms_allowed"] is False
    assert report["selection_policy"]["position_binding_is_source_play_claim"] is False
    for row in report["selected"]:
        assert row["paid_model_call"] is False
        assert row["registry_write"] is False
        assert row["website_write"] is False
        assert row["scheduled"] is False
        assert row["published"] is False
