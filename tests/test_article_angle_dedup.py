from engine.article_angles import apply_article_angle
from engine.semantic_dedup import structural_similarity


def _stage():
    return {
        "index": 1,
        "atom": "span_range",
        "label": "跨度2–6",
        "before_space": 1000,
        "after_space": 436,
        "excluded_space": 564,
        "support_mode": "verified_rule_calculation",
        "params": {"min": 2, "max": 6},
    }


def _base():
    return {
        "blueprint_id": "BP-base",
        "article_id": "LCM-IDEA-base000000000001",
        "fingerprint": "f" * 64,
        "angle_signature": "base-angle",
        "status": "ready_for_draft",
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "lottery": "时时彩",
        "play": "后三直选",
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "technique_atoms": ["span_range"],
        "primary_keyword": "分分彩后三直选跨度技巧",
        "secondary_keywords": [],
        "search_intent": "legacy",
        "slug_seed": "ffc-test",
        "case_structure": "selector=后三;metrics=span;scope=mechanics_only",
        "production_filter_contract": {
            "mode": "single_stage",
            "filter_pipeline_result": {
                "starting_space": 1000,
                "final_space": 436,
                "total_excluded": 564,
                "stage_count": 1,
                "stages": [_stage()],
            },
        },
    }


def _formal(record):
    row = dict(record)
    row["status"] = "approved"
    row["angle_approval_passed"] = True
    return row


def test_different_audited_angles_are_a_distinct_structural_dimension():
    left = apply_article_angle(_base(), "space_math")
    right = apply_article_angle(_base(), "execution_checklist")
    score, reasons = structural_similarity(left, _formal(right))
    assert score <= 0.80
    assert score < 0.82
    assert "different_audited_information_gain" in reasons


def test_same_audited_angle_remains_strictly_duplicate_like():
    left = apply_article_angle(_base(), "space_math")
    right = dict(left)
    right["article_id"] = "OTHER"
    right["fingerprint"] = "e" * 64
    score, reasons = structural_similarity(left, _formal(right))
    assert score >= 0.82
    assert "same_audited_information_gain" in reasons


def test_approved_owner_without_angle_gate_pass_uses_legacy_structural_score():
    left = apply_article_angle(_base(), "space_math")
    right = apply_article_angle(_base(), "execution_checklist")
    right["status"] = "approved"
    right["angle_approval_passed"] = False
    score, reasons = structural_similarity(left, right)
    assert score >= 0.82
    assert "different_audited_information_gain" not in reasons


def test_legacy_records_are_not_granted_angle_separation():
    left = apply_article_angle(_base(), "space_math")
    legacy = _base()
    legacy["article_id"] = "LEGACY"
    legacy["fingerprint"] = "a" * 64
    legacy["status"] = "approved"
    score, reasons = structural_similarity(left, legacy)
    assert score >= 0.82
    assert not any("audited_information_gain" in reason for reason in reasons)
