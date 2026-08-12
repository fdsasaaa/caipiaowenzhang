from __future__ import annotations

import json

from engine.blueprints import blueprint_from_plan
from engine.draft_packets import build_draft_packet
from engine.editorial_quality import evaluate_editorial
from engine.production_evidence import normalize_production_claim_metadata
from engine.production_filter_contract import assess_primary_filter_contract


def _plan(*, play: str = "五星直选", selector: str = "五星", atoms: list[str] | None = None) -> dict:
    atoms = atoms or ["position_filter", "span_range"]
    return {
        "status": "ready_mechanics_only",
        "provider_id": "",
        "lottery": "时时彩",
        "play": play,
        "content_type": "technique_article",
        "technique_family": "TEST-PRODUCTION-FILTER-FAMILY",
        "technique_atoms": atoms,
        "positions": [selector],
        "resolved_selector": selector,
        "selector_basis": "test_fixture",
        "angle_signature": "test-production-filter-contract",
        "case_plan": {
            "case_engine_ready": True,
            "resolved_selector": selector,
            "selector_basis": "test_fixture",
            "supported": [
                {"atom": atom, "metric": atom}
                for atom in atoms
                if atom != "position_filter"
            ],
            "unsupported": [],
        },
        "allowed_case_scope": "mechanics_only",
        "rule_refs": ["SSC-HIST-MECH-5STAR-DIRECT-V1"],
        "source_refs": ["BRBCW-TEST"],
        "source_support_count": 29,
        "source_risk_rate": 0.379,
    }


def test_five_star_span_contract_has_real_machine_reduction():
    result = assess_primary_filter_contract(
        play="五星直选",
        selector="五星",
        atoms=["position_filter", "span_range"],
    )
    assert result["status"] == "ready"
    spec = result["spec"]
    assert spec["atom"] == "span_range"
    assert spec["metric"] == "span"
    assert spec["op"] == "span_range"
    assert spec["params"] == {"min": 4, "max": 8}
    assert spec["starting_space"] == 100000
    assert spec["after_filter_space"] == 79620
    assert spec["excluded_space"] == 20380
    assert spec["basis"] == "system_research_prefrozen"
    assert spec["parameter_owner"] == "system_research"
    assert spec["source_parameter_attribution"] is False
    assert spec["parameter_freeze_before_observation"] is True


def test_single_position_odd_even_contract_is_supported_but_sum_span_are_not():
    parity = assess_primary_filter_contract(
        play="定位胆",
        selector="个位",
        atoms=["position_filter", "odd_even_filter"],
    )
    assert parity["status"] == "ready"
    assert parity["spec"]["starting_space"] == 10
    assert parity["spec"]["after_filter_space"] == 5

    span = assess_primary_filter_contract(
        play="定位胆",
        selector="个位",
        atoms=["position_filter", "span_range"],
    )
    assert span["status"] == "blocked"
    assert span["reason"] == "primary_filter_parameter_policy_missing"


def test_multiple_filters_require_multistage_contract_instead_of_silent_single_stage():
    result = assess_primary_filter_contract(
        play="后三直选",
        selector="后三",
        atoms=["position_filter", "sum_range", "span_range"],
    )
    assert result["status"] == "blocked"
    assert result["reason"] == "multiple_filter_atoms_require_multistage_contract"


def test_sample_dependent_filter_remains_fail_closed():
    result = assess_primary_filter_contract(
        play="后三直选",
        selector="后三",
        atoms=["position_filter", "omission_threshold"],
    )
    assert result["status"] == "blocked"
    assert result["reason"] == "filter_atom_requires_source_or_sample_parameter_contract"


def test_group_play_cannot_reuse_ordered_direct_primary_filter_domain():
    result = assess_primary_filter_contract(
        play="后三组选6",
        selector="后三",
        atoms=["position_filter", "span_range"],
    )
    assert result["status"] == "blocked"
    assert result["reason"] == "primary_filter_target_domain_not_supported"


def test_blueprint_carries_machine_filter_spec_into_draft_packet():
    blueprint = blueprint_from_plan(_plan())
    assert blueprint["status"] == "ready_for_draft", blueprint["blockers"]
    spec = blueprint["primary_filter_spec"]
    assert spec["starting_space"] == 100000
    assert spec["after_filter_space"] == 79620
    assert "primary_filter=" in blueprint["case_structure"]

    packet = build_draft_packet(blueprint)
    assert packet["practicality"]["primary_filter_spec"] == spec
    assert packet["case_bundle"]["primary_filter_spec"] == spec


def test_structured_filter_counts_can_earn_full_editorial_score_without_model_guessing():
    blueprint = blueprint_from_plan(_plan())
    packet = build_draft_packet(blueprint)
    spec = packet["practicality"]["primary_filter_spec"]
    article = {
        "content": (
            "<h2>实际怎么操作</h2>"
            f"<p>先固定五星直选的{spec['starting_space']}个有序结果，再按系统预冻结的跨度4–8筛选，"
            f"剩下{spec['after_filter_space']}个，排除{spec['excluded_space']}个。</p>"
        ),
        "practical_guidance": {
            "steps": ["固定五星直选。", "冻结跨度4–8。", "逐个计算最大值减最小值。", "核对筛选后空间。"],
            "starting_space": f"{spec['starting_space']}个五星直选有序结果",
            "after_primary_filter_space": f"筛选后{spec['after_filter_space']}个结果",
            "parameter_freeze_rule": "跨度4–8由系统在观察演示样本前固定。",
            "stop_condition": "完成这一层后停止，不再追加过滤器。",
            "next_step_policy": "只有新增条件具有已验证规则或证据并可复算时才允许继续。",
        },
    }
    report = evaluate_editorial(packet, article)
    assert report.passed is True, report.errors
    assert report.score == 100


def test_pure_editorial_disclaimer_source_metadata_is_normalized_without_rewriting_content():
    article = {
        "content": "<p>正文保持原样。</p>",
        "claim_evidence": [{
            "claim_text": "本文只讲分分彩五星直选的玩法和筛选步骤，不讨论未核验的平台经济参数。",
            "claim_type": "editorial",
            "support_type": "source_unverified",
            "support_refs": ["BRBCW-002590"],
            "evidence_note": "provider classified this as source metadata",
        }],
    }
    normalized = normalize_production_claim_metadata({}, article)
    assert normalized["content"] == article["content"]
    row = normalized["claim_evidence"][0]
    assert row["support_type"] == "editorial"
    assert row["support_refs"] == []
    assert article["claim_evidence"][0]["support_type"] == "source_unverified"


def test_actual_source_claim_is_never_normalized_even_if_model_calls_it_editorial():
    article = {
        "content": "<p>来源提到跨度方法。</p>",
        "claim_evidence": [{
            "claim_text": "来源提到跨度方法，但尚未独立验证。",
            "claim_type": "editorial",
            "support_type": "source_unverified",
            "support_refs": ["BRBCW-002590"],
            "evidence_note": "real source provenance",
        }],
    }
    normalized = normalize_production_claim_metadata({}, article)
    assert normalized["claim_evidence"][0]["support_type"] == "source_unverified"
    assert normalized["claim_evidence"][0]["support_refs"] == ["BRBCW-002590"]


def test_performance_claim_is_never_normalized_as_editorial_disclaimer():
    article = {
        "content": "<p>命中率更高。</p>",
        "claim_evidence": [{
            "claim_text": "本文只讲这个方法，但命中率更高。",
            "claim_type": "editorial",
            "support_type": "source_unverified",
            "support_refs": ["BRBCW-002590"],
            "evidence_note": "unsafe",
        }],
    }
    normalized = normalize_production_claim_metadata({}, article)
    assert normalized["claim_evidence"][0]["support_type"] == "source_unverified"
