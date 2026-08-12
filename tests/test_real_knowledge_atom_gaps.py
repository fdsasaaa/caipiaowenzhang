from __future__ import annotations

from engine.real_knowledge_atom_gaps import automation_class, build_atom_gap_report
from engine.technique_semantics import load_semantics


def test_gap_report_preserves_known_full_archive_funnel():
    report = build_atom_gap_report()
    assert report["total_families"] == 759
    assert report["basic_source_gate_families"] == 35
    assert report["families_blocked_by_unbound_atoms"] == 30
    assert report["paid_model_call"] is False
    assert report["registry_write"] is False
    assert report["website_write"] is False
    assert report["scheduled"] is False
    assert report["published"] is False


def test_only_semantics_ready_sample_independent_atoms_are_marked_deterministic_candidates():
    report = build_atom_gap_report()
    candidate_atoms = {row["atom"] for row in report["deterministic_semantics_ready_candidates"]}
    assert candidate_atoms.issubset({"repeat_number", "neighbor_number"})
    assert candidate_atoms
    for row in report["deterministic_semantics_ready_candidates"]:
        assert row["semantics_defined"] is True
        assert row["automation_class"] == "deterministic_semantics_ready_needs_filter_operator"


def test_sample_dependent_atoms_never_become_deterministic_candidates():
    report = build_atom_gap_report()
    rows = {row["atom"]: row for row in report["ranked_unbound_atoms"]}
    for atom in ("cold_hot_split", "frequency_window", "omission_threshold"):
        if atom in rows:
            assert rows[atom]["automation_class"] == "sample_parameter_contract_required"
            assert rows[atom]["structural_strict_multistage_unlock_if_only_atom_added"] >= 0


def test_missing_semantics_atoms_remain_fail_closed():
    semantics = load_semantics().get("atoms") or {}
    for atom in ("progressive_staking", "follow_after_event", "kill_candidate", "stop_loss", "stop_win"):
        assert automation_class(atom, semantics) == "missing_semantics_or_domain_contract"


def test_unlock_estimates_do_not_claim_implementation():
    report = build_atom_gap_report()
    for row in report["ranked_unbound_atoms"]:
        assert row["automation_class"] != "already_executable"
        assert row["blocked_family_count"] >= row["bindable_blocked_family_count"]
        assert row["structural_bindable_unlock_if_only_atom_added"] >= row["structural_strict_multistage_unlock_if_only_atom_added"]


def test_ranking_is_deterministic():
    first = build_atom_gap_report()["ranked_unbound_atoms"]
    second = build_atom_gap_report()["ranked_unbound_atoms"]
    assert first == second
