from engine.article_angles import (
    ANGLE_CONTRACT_VERSION,
    allowed_angle_types,
    apply_article_angle,
    audited_angle_type,
    expand_article_angle_variants,
    same_audited_angle,
)


def _stage(index, atom, label, before, after, *, sample=False, params=None):
    return {
        "index": index,
        "atom": atom,
        "label": label,
        "before_space": before,
        "after_space": after,
        "excluded_space": before - after,
        "support_mode": "synthetic_case_calculation" if sample else "verified_rule_calculation",
        "params": params or {},
    }


def _blueprint(stages):
    start = stages[0]["before_space"]
    final = stages[-1]["after_space"]
    return {
        "blueprint_id": "BP-base",
        "article_id": "LCM-IDEA-base000000000001",
        "fingerprint": "f" * 64,
        "angle_signature": "base-angle-signature",
        "status": "ready_for_draft",
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "lottery": "时时彩",
        "play": "后三直选",
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "technique_family": "FAM-test",
        "technique_atoms": [stage["atom"] for stage in stages],
        "primary_keyword": "分分彩后三直选和值跨度技巧",
        "secondary_keywords": ["分分彩技巧"],
        "search_intent": "legacy",
        "summary_goal": "legacy",
        "outline": ["legacy"],
        "slug_seed": "ffc-test",
        "case_structure": "selector=后三;metrics=sum,span;scope=mechanics_only",
        "production_filter_contract": {
            "mode": "multistage" if len(stages) > 1 else "single_stage",
            "filter_pipeline_result": {
                "starting_space": start,
                "final_space": final,
                "total_excluded": start - final,
                "stage_count": len(stages),
                "stages": stages,
            },
        },
    }


def test_static_contract_exposes_four_genuine_angles():
    bp = _blueprint([_stage(1, "span_range", "跨度2–6", 1000, 436)])
    assert allowed_angle_types(bp) == [
        "mechanics_case", "space_math", "execution_checklist", "parameter_boundary"
    ]
    variants = expand_article_angle_variants(bp)
    assert len(variants) == 4
    assert len({row["article_id"] for row in variants}) == 4
    assert len({row["primary_keyword"] for row in variants}) == 4
    assert variants[0]["article_id"] == bp["article_id"]
    assert variants[0]["angle_signature"] == bp["angle_signature"]
    assert all(row["article_angle_contract_version"] == ANGLE_CONTRACT_VERSION for row in variants)
    assert all(row["angle_contract_verified"] is True for row in variants)


def test_multistage_sample_contract_exposes_all_six_angles():
    bp = _blueprint([
        _stage(1, "sum_range", "和值8–19", 1000, 760, params={"min": 8, "max": 19}),
        _stage(2, "frequency_window", "近12期频率Top-5", 760, 320, sample=True, params={"lookback": 12, "top_n": 5}),
    ])
    assert allowed_angle_types(bp) == [
        "mechanics_case", "space_math", "execution_checklist", "parameter_boundary",
        "multistage_order", "sample_provenance",
    ]
    sample = apply_article_angle(bp, "sample_provenance")
    contract = sample["article_angle_contract"]
    assert sample["article_id"].startswith("LCM-ANGLE-")
    assert sample["primary_keyword"].endswith("演示案例")
    assert contract["required_machine_facts"]["starting_space"] == 1000
    assert contract["required_machine_facts"]["final_space"] == 320
    assert contract["required_machine_facts"]["excluded_space"] == 680
    assert contract["required_machine_facts"]["sample_stage_labels"] == ["近12期频率Top-5"]
    assert contract["source_parameter_attribution_allowed"] is False
    assert contract["predictive_advantage_claimed"] is False


def test_parameter_boundary_text_is_truthful_for_static_vs_sample_contracts():
    static = apply_article_angle(
        _blueprint([_stage(1, "span_range", "跨度2–6", 1000, 436)]),
        "parameter_boundary",
    )
    assert "系统研究预设" in static["title"]
    assert "演示样本算出来" not in static["title"]

    sample = apply_article_angle(
        _blueprint([_stage(1, "frequency_window", "近12期频率Top-5", 1000, 500, sample=True, params={"lookback": 12, "top_n": 5})]),
        "parameter_boundary",
    )
    assert "演示样本算出来" in sample["title"]


def test_audited_angle_identity_is_fail_closed_for_formal_owners():
    candidate = apply_article_angle(
        _blueprint([_stage(1, "span_range", "跨度2–6", 1000, 436)]),
        "space_math",
    )
    candidate["status"] = "draft"
    assert audited_angle_type(candidate) == "space_math"

    owner = dict(candidate)
    owner["status"] = "approved"
    owner.pop("angle_approval_passed", None)
    assert audited_angle_type(owner) is None
    owner["angle_approval_passed"] = False
    assert audited_angle_type(owner) is None
    owner["angle_approval_passed"] = True
    assert audited_angle_type(owner) == "space_math"


def test_same_audited_angle_requires_two_verified_contracts():
    base = _blueprint([_stage(1, "span_range", "跨度2–6", 1000, 436)])
    left = apply_article_angle(base, "space_math")
    right = apply_article_angle(base, "execution_checklist")
    assert same_audited_angle(left, right) is False
    right["angle_contract_verified"] = False
    assert same_audited_angle(left, right) is None
