from __future__ import annotations

from types import SimpleNamespace

import engine.production_controller as controller
from engine.ai_generation_v22 import _normalize_multistage_article, _pipeline_evidence_rows
from engine.production_controller import _packet_with_cluster_metadata, execute_production_plan
from engine.production_filter_contract import build_production_filter_contract


def _base_blueprint(atoms: list[str]) -> dict:
    return {
        "article_id": "CTRL-MULTI-001",
        "blueprint_id": "BP-CTRL-MULTI-001",
        "provider_id": "",
        "lottery": "时时彩",
        "play": "后三直选",
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "technique_family": "FAM-CTRL-MULTI",
        "technique_atoms": atoms,
        "resolved_selector": "后三",
        "selector_basis": "test_fixture",
        "angle_signature": "ctrl-multi-angle",
        "title": "分分彩后三直选和值跨度技巧：按顺序复算多层筛选",
        "slug_seed": "ffc-last3-multistage",
        "primary_keyword": "分分彩后三和值跨度技巧",
        "secondary_keywords": ["分分彩技巧"],
        "search_intent": "学习多层筛选并看懂可复算案例",
        "information_gain_type": "method_mechanics_and_reproducible_case",
        "summary_goal": "解释多层筛选如何按顺序复算。",
        "outline": ["玩法规则", "第一层", "第二层", "实际怎么操作", "风险说明"],
        "case_structure": "selector=后三;scope=mechanics_only",
        "case_scope": "mechanics_only",
        "rule_refs": ["SSC-HIST-MECH-3STAR-LAST-V1"],
        "source_refs": ["BRBCW-TEST"],
        "fingerprint": "ctrl-multi-fingerprint",
        "status": "ready_for_draft",
        "blockers": [],
        "editorial_contract_version": "1.1",
        "primary_seo_cluster_id": "ffc_research",
        "secondary_seo_cluster_ids": [],
    }


def _attach_contract(blueprint: dict, case_bundle: dict) -> dict:
    contract = build_production_filter_contract(blueprint, case_bundle)
    blueprint["production_filter_contract"] = contract
    blueprint["primary_filter_spec"] = contract["primary_filter_spec"]
    if contract["mode"] == "multistage":
        blueprint["filter_pipeline_spec"] = contract["filter_pipeline_spec"]
        blueprint["filter_pipeline_result"] = contract["filter_pipeline_result"]
    return blueprint


def _blueprint() -> dict:
    return _attach_contract(
        _base_blueprint(["sum_range", "span_range"]),
        {"label": "演示数据，不是真实开奖记录。", "selector": "后三", "sample_size": 12, "draws": []},
    )


def _sample_blueprint() -> dict:
    return _attach_contract(
        _base_blueprint(["sum_range", "frequency_window"]),
        {
            "label": "演示数据，不是真实开奖记录。",
            "selector": "后三",
            "sample_size": 12,
            "draws": [],
            "frequency": {"sample_size": 12, "top_frequency_digits": [7, 2, 5]},
        },
    )


def _package() -> dict:
    return {
        "article_id": "CTRL-MULTI-001",
        "status": "approved",
        "title": "分分彩后三和值跨度技巧",
        "seo_title": "分分彩后三和值跨度技巧",
        "meta_description": "分分彩后三和值跨度技巧复算案例。",
        "primary_keyword": "分分彩后三和值跨度技巧",
        "secondary_keywords": ["分分彩技巧"],
        "search_intent": "学习多层复算",
        "summary": "分分彩多层复算案例。",
        "tags": ["分分彩"],
        "content": "<p>演示数据，不是真实开奖记录。</p>",
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "primary_seo_cluster_id": "ffc_research",
    }


def test_controller_packet_promotes_multi_method_contract_to_v22():
    packet = _packet_with_cluster_metadata(_blueprint())
    assert packet["contract_version"] == "2.2-multistage"
    result = packet["practicality"]["filter_pipeline_result"]
    assert result["stage_count"] == 2
    assert result["starting_space"] == 1000
    assert result["final_space"] == 396
    assert packet["practicality"]["minimum_concrete_steps"] >= 5
    assert packet["source_use"]["production_parameter_source_attribution_allowed"] is False
    assert packet["output_contract"]["require_multistage_pipeline"] is True


def test_static_and_sample_pipeline_evidence_use_different_support_types():
    packet = _packet_with_cluster_metadata(_sample_blueprint())
    rows = _pipeline_evidence_rows(packet)
    static_rows = [row for row in rows if "第1层候选空间" in row["claim_text"]]
    sample_rows = [row for row in rows if "第2层候选空间" in row["claim_text"]]
    overall_rows = [row for row in rows if row["claim_text"].startswith("完整多层筛选")]
    assert static_rows and static_rows[0]["support_type"] == "verified_rule"
    assert static_rows[0]["support_refs"] == ["SSC-HIST-MECH-3STAR-LAST-V1"]
    assert sample_rows and sample_rows[0]["support_type"] == "synthetic_case"
    assert sample_rows[0]["support_refs"] == ["case_bundle"]
    assert overall_rows and overall_rows[0]["support_type"] == "synthetic_case"
    assert overall_rows[0]["support_refs"] == ["case_bundle"]


def test_multistage_normalizer_moves_sample_stage_claim_to_case_bundle_without_rewriting_content():
    packet = _packet_with_cluster_metadata(_sample_blueprint())
    stage = packet["practicality"]["filter_pipeline_result"]["stages"][1]
    claim = f"第2层候选空间从{stage['before_space']}个缩到{stage['after_space']}个，排除{stage['excluded_space']}个。"
    article = {
        "content": "<p>正文保持不变。</p>",
        "claim_evidence": [{
            "claim_text": claim,
            "claim_type": "calculation",
            "support_type": "verified_rule",
            "support_refs": ["SSC-HIST-MECH-3STAR-LAST-V1"],
            "evidence_note": "provider guessed wrong provenance",
        }],
    }
    normalized = _normalize_multistage_article(article, packet)
    assert normalized["content"] == article["content"]
    row = next(row for row in normalized["claim_evidence"] if row["claim_text"] == claim)
    assert row["support_type"] == "synthetic_case"
    assert row["support_refs"] == ["case_bundle"]


def test_default_controller_route_uses_multistage_generator_for_v22_packet(monkeypatch):
    calls = {"multi": 0, "approve": 0}

    def fake_multi(packet, **kwargs):
        calls["multi"] += 1
        assert packet["contract_version"] == "2.2-multistage"
        return SimpleNamespace(article={"article_id": packet["article_id"], "content": "<p>演示数据，不是真实开奖记录。</p>"})

    monkeypatch.setattr(controller, "generate_multistage_article", fake_multi)
    monkeypatch.setattr(controller, "evaluate_multistage", lambda packet, article: SimpleNamespace(passed=True, score=100, errors=[]))

    def fake_approve(packet, article):
        calls["approve"] += 1
        return SimpleNamespace(approved=True, publish_package=_package(), status="approved", quality_score=100, editorial_score=100, errors=[])

    plan = {"target_new_formal_articles": 1, "batch_size": 1, "candidates": [{"priority_score": 100, "blueprint": _blueprint()}]}
    result = execute_production_plan(
        plan,
        approve_fn=fake_approve,
        stage_fn=lambda package: {"status": "staged", "article_id": package["article_id"]},
    )
    assert calls == {"multi": 1, "approve": 1}
    assert result["formal_inventory_staged"] == 1
    assert result["multistage_failed"] == 0
    assert result["multistage_score_average"] == 100


def test_multistage_failure_blocks_standard_approval_and_inventory(monkeypatch):
    calls = {"approve": 0, "stage": 0}
    monkeypatch.setattr(
        controller,
        "generate_multistage_article",
        lambda packet, **kwargs: SimpleNamespace(article={"article_id": packet["article_id"], "content": "<p>演示数据，不是真实开奖记录。</p>"}),
    )
    monkeypatch.setattr(controller, "evaluate_multistage", lambda packet, article: SimpleNamespace(passed=False, score=70, errors=["第二层空间不匹配"]))

    def fake_approve(packet, article):
        calls["approve"] += 1
        raise AssertionError("standard approval must not run after failed multistage gate")

    def fake_stage(package):
        calls["stage"] += 1
        raise AssertionError("inventory must not run")

    plan = {"target_new_formal_articles": 1, "batch_size": 1, "candidates": [{"priority_score": 100, "blueprint": _blueprint()}]}
    result = execute_production_plan(plan, approve_fn=fake_approve, stage_fn=fake_stage)
    assert calls == {"approve": 0, "stage": 0}
    assert result["formal_inventory_staged"] == 0
    assert result["approval_failed"] == 1
    assert result["multistage_failed"] == 1
    assert result["results"][0]["status"] == "rejected_multistage"


def test_explicit_custom_generator_still_takes_precedence(monkeypatch):
    calls = {"custom": 0, "multi": 0}

    def custom_generate(packet, **kwargs):
        calls["custom"] += 1
        return SimpleNamespace(article={"article_id": packet["article_id"], "content": "<p>演示数据，不是真实开奖记录。</p>"})

    def should_not_route(packet, **kwargs):
        calls["multi"] += 1
        raise AssertionError("custom generate_fn must win")

    monkeypatch.setattr(controller, "generate_multistage_article", should_not_route)
    monkeypatch.setattr(controller, "evaluate_multistage", lambda packet, article: SimpleNamespace(passed=True, score=100, errors=[]))

    plan = {"target_new_formal_articles": 1, "batch_size": 1, "candidates": [{"priority_score": 100, "blueprint": _blueprint()}]}
    execute_production_plan(
        plan,
        generate_fn=custom_generate,
        approve_fn=lambda packet, article: SimpleNamespace(approved=True, publish_package=_package(), status="approved", quality_score=100, editorial_score=100, errors=[]),
        stage_fn=lambda package: {"status": "staged", "article_id": package["article_id"]},
    )
    assert calls == {"custom": 1, "multi": 0}
