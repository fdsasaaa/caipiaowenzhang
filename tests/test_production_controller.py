from __future__ import annotations

from types import SimpleNamespace

import pytest

from engine.production_controller import (
    ProductionControllerError,
    execute_production_plan,
    partition_batches,
    resolve_batch_size,
    target_band,
)


def _blueprint(article_id: str = "CTRL-001") -> dict:
    return {
        "article_id": article_id,
        "blueprint_id": "BP-CTRL-001",
        "provider_id": "",
        "lottery": "时时彩",
        "play": "后三直选",
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "content_type": "technique_article",
        "site_category_key": "tzjq",
        "technique_family": "FAM-CTRL",
        "technique_atoms": ["sum_range"],
        "resolved_selector": "后三",
        "angle_signature": "ctrl-angle-001",
        "title": "分分彩后三直选技巧：和值区间怎么复算",
        "slug_seed": "ffc-last3-sum",
        "primary_keyword": "分分彩后三和值技巧",
        "secondary_keywords": ["分分彩技巧"],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "information_gain_type": "method_mechanics_and_reproducible_case",
        "summary_goal": "解释和值区间如何复算。",
        "outline": ["玩法规则", "计算方法", "案例", "风险说明"],
        "case_structure": "selector=后三;metrics=sum;scope=mechanics_only",
        "case_scope": "mechanics_only",
        "rule_refs": ["R-CTRL-1"],
        "source_refs": ["S-CTRL-1"],
        "fingerprint": "ctrl-fingerprint-001",
        "status": "ready_for_draft",
        "blockers": [],
        "editorial_contract_version": "1.0",
        "primary_seo_cluster_id": "ffc_research",
        "secondary_seo_cluster_ids": [],
    }


def _package(article_id: str = "CTRL-001") -> dict:
    content = "<p>演示数据，不是真实开奖记录。本文只解释可复算步骤，不代表预测优势。</p>"
    return {
        "article_id": article_id,
        "status": "approved",
        "title": "分分彩后三直选技巧：和值区间怎么复算",
        "seo_title": "分分彩后三和值技巧",
        "meta_description": "分分彩后三和值技巧案例说明。",
        "primary_keyword": "分分彩后三和值技巧",
        "secondary_keywords": ["分分彩技巧"],
        "search_intent": "学习具体投注技巧并看懂可复算案例",
        "summary": "分分彩可复算案例。",
        "tags": ["分分彩"],
        "content": content,
        "subject_lottery": "分分彩",
        "subject_play": "后三直选",
        "primary_seo_cluster_id": "ffc_research",
    }


def test_target_bands_and_recommended_limits():
    assert target_band(200) == "ordinary"
    assert target_band(500) == "ordinary"
    assert target_band(501) == "large"
    assert target_band(2000) == "large"
    assert target_band(2001) == "ultra"
    with pytest.raises(ProductionControllerError):
        target_band(0)


def test_internal_batch_policy():
    assert resolve_batch_size(200) == 25
    assert resolve_batch_size(9) == 9
    assert resolve_batch_size(200, 20) == 20
    assert resolve_batch_size(200, 30) == 30
    with pytest.raises(ProductionControllerError):
        resolve_batch_size(200, 31)


def test_partition_uses_small_safe_internal_batches():
    assert partition_batches(200, 25) == [25] * 8
    assert partition_batches(500, 25) == [25] * 20
    assert partition_batches(52, 25) == [25, 25, 2]


def test_execute_controller_stages_approved_without_website_side_effects(monkeypatch):
    # This test verifies controller staging/side-effect semantics, not live dedup.
    # Keep it independent from mutable production Registry contents.
    monkeypatch.setattr("engine.production_controller.duplicate_candidates", lambda blueprint: [])
    monkeypatch.setattr("engine.production_controller.structural_duplicate_candidates", lambda blueprint: [])
    seen = {}

    def fake_generate(packet, **kwargs):
        seen["packet"] = packet
        return SimpleNamespace(article={"article_id": "CTRL-001"})

    def fake_approve(packet, article):
        return SimpleNamespace(
            approved=True,
            publish_package=_package(),
            status="approved",
            quality_score=100,
            editorial_score=100,
            errors=[],
        )

    def fake_stage(package):
        return {"status": "staged", "article_id": package["article_id"], "path": "articles/approved/CTRL-001.json"}

    plan = {
        "target_new_formal_articles": 1,
        "batch_size": 1,
        "candidates": [{"priority_score": 100, "blueprint": _blueprint()}],
    }
    result = execute_production_plan(
        plan,
        generate_fn=fake_generate,
        approve_fn=fake_approve,
        stage_fn=fake_stage,
    )
    assert result["status"] == "PASS_TARGET_REACHED"
    assert result["formal_inventory_staged"] == 1
    assert result["website_sync_attempted"] is False
    assert result["scheduled"] is False
    assert result["published"] is False
    assert seen["packet"]["immutable_facts"]["primary_seo_cluster_id"] == "ffc_research"


def test_controller_does_not_count_failed_approval_toward_target(monkeypatch):
    # This test verifies approval accounting, not live dedup. Isolate the Registry.
    monkeypatch.setattr("engine.production_controller.duplicate_candidates", lambda blueprint: [])
    monkeypatch.setattr("engine.production_controller.structural_duplicate_candidates", lambda blueprint: [])

    def fake_generate(packet, **kwargs):
        return SimpleNamespace(article={"article_id": packet["article_id"]})

    def fake_approve(packet, article):
        return SimpleNamespace(
            approved=False,
            publish_package=None,
            status="rejected",
            quality_score=80,
            editorial_score=80,
            errors=["quality gate"],
        )

    plan = {
        "target_new_formal_articles": 1,
        "batch_size": 1,
        "candidates": [{"priority_score": 90, "blueprint": _blueprint()}],
    }
    result = execute_production_plan(plan, generate_fn=fake_generate, approve_fn=fake_approve)
    assert result["formal_inventory_staged"] == 0
    assert result["approval_failed"] == 1
    assert result["status"] == "PARTIAL_STOPPED"



def test_controller_blocks_live_duplicate_before_provider(monkeypatch):
    calls = {"generate": 0}

    def fake_generate(packet, **kwargs):
        calls["generate"] += 1
        return SimpleNamespace(article={"article_id": packet["article_id"]}, response_id="resp-never")

    monkeypatch.setattr(
        "engine.production_controller.duplicate_candidates",
        lambda blueprint: [SimpleNamespace(article_id="LIVE-001", score=0.84, reason="lexical/core overlap")],
    )
    monkeypatch.setattr("engine.production_controller.structural_duplicate_candidates", lambda blueprint: [])
    plan = {
        "target_new_formal_articles": 1,
        "batch_size": 1,
        "candidates": [{"priority_score": 90, "blueprint": _blueprint("CTRL-DUP-001")}],
    }
    result = execute_production_plan(plan, generate_fn=fake_generate)
    assert calls["generate"] == 0
    assert result["attempted"] == 0
    assert result["generated"] == 0
    assert result["pre_generation_duplicate_blocked"] == 1
    assert result["results"][0]["status"] == "pre_generation_duplicate_blocked"
    assert result["results"][0]["duplicate_article_id"] == "LIVE-001"


def test_controller_rechecks_registry_before_each_candidate(monkeypatch):
    duplicate_checks = {"count": 0}
    generation_calls = {"count": 0}

    def fake_duplicate(blueprint):
        duplicate_checks["count"] += 1
        if duplicate_checks["count"] == 1:
            return []
        return [SimpleNamespace(article_id="CTRL-FIRST", score=0.81, reason="lexical/core overlap")]

    def fake_generate(packet, **kwargs):
        generation_calls["count"] += 1
        return SimpleNamespace(article={"article_id": packet["article_id"]}, response_id=f"resp-{generation_calls['count']}")

    def fake_approve(packet, article):
        package = _package(article["article_id"])
        package["provider_response_id"] = article.get("provider_response_id")
        return SimpleNamespace(approved=True, publish_package=package, status="approved", quality_score=100, editorial_score=100, errors=[])

    def fake_stage(package):
        return {"status": "staged", "article_id": package["article_id"]}

    monkeypatch.setattr("engine.production_controller.duplicate_candidates", fake_duplicate)
    monkeypatch.setattr("engine.production_controller.structural_duplicate_candidates", lambda blueprint: [])
    plan = {
        "target_new_formal_articles": 2,
        "batch_size": 2,
        "candidates": [
            {"priority_score": 100, "blueprint": _blueprint("CTRL-FIRST")},
            {"priority_score": 90, "blueprint": _blueprint("CTRL-SECOND")},
        ],
    }
    result = execute_production_plan(plan, generate_fn=fake_generate, approve_fn=fake_approve, stage_fn=fake_stage)
    assert duplicate_checks["count"] == 2
    assert generation_calls["count"] == 1
    assert result["attempted"] == 1
    assert result["formal_inventory_staged"] == 1
    assert result["pre_generation_duplicate_blocked"] == 1


def test_controller_records_provider_response_id(monkeypatch):
    monkeypatch.setattr("engine.production_controller.duplicate_candidates", lambda blueprint: [])
    monkeypatch.setattr("engine.production_controller.structural_duplicate_candidates", lambda blueprint: [])
    seen = {}

    def fake_generate(packet, **kwargs):
        return SimpleNamespace(article={"article_id": packet["article_id"]}, response_id="resp-controller-audit-001")

    def fake_approve(packet, article):
        seen["article_response_id"] = article.get("provider_response_id")
        package = _package(article["article_id"])
        package["provider_response_id"] = article.get("provider_response_id")
        return SimpleNamespace(approved=True, publish_package=package, status="approved", quality_score=100, editorial_score=100, errors=[])

    def fake_stage(package):
        seen["package_response_id"] = package.get("provider_response_id")
        return {"status": "staged", "article_id": package["article_id"]}

    plan = {
        "target_new_formal_articles": 1,
        "batch_size": 1,
        "candidates": [{"priority_score": 100, "blueprint": _blueprint("CTRL-AUDIT-001")}],
    }
    result = execute_production_plan(plan, generate_fn=fake_generate, approve_fn=fake_approve, stage_fn=fake_stage)
    assert seen["article_response_id"] == "resp-controller-audit-001"
    assert seen["package_response_id"] == "resp-controller-audit-001"
    assert result["provider_response_ids"] == ["resp-controller-audit-001"]
    assert result["results"][0]["provider_response_id"] == "resp-controller-audit-001"
