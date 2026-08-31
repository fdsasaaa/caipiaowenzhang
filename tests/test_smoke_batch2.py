import json
from pathlib import Path

from engine import approval, blueprints, quality
from engine.approval import evaluate_for_approval
from engine.title_seo import TITLE_SEO_CONTRACT_VERSION
from engine.title_seo_runtime import suggest_title_candidates
from engine.blueprints import blueprint_from_plan
from engine.draft_packets import build_draft_packet
from engine.planner import plan_articles

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "smoke" / "batch2"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _matching_plan(spec: dict) -> dict:
    result = plan_articles("", "时时彩", spec["rule_play"], 300)
    matches = [
        p for p in result.get("plans", [])
        if p.get("technique_family") == spec["family_id"]
        and p.get("resolved_selector") == spec["resolved_selector"]
    ]
    assert matches, f"source family/selector not found: {spec}"
    plan = dict(matches[0])
    assert plan["status"] == "ready_mechanics_only"
    assert plan["case_plan"]["case_engine_ready"] is True
    assert spec["source_ref"] in plan["source_refs"]
    assert plan["source_support_count"] == spec["source_support_count"]
    assert abs(plan["source_risk_rate"] - spec["source_risk_rate"]) < 1e-9
    assert plan["technique_atoms"] == spec["atoms"]
    plan["subject_lottery"] = "分分彩"
    plan["subject_play"] = spec["subject_play"]
    return plan


def test_batch2_uses_real_source_families_and_passes_full_approval(monkeypatch):
    # This is a frozen historical package regression, not a live production
    # availability test. New formal articles must not retroactively invalidate
    # the 2026-08-11 fixture. Live dedup itself is tested separately.
    monkeypatch.setattr(blueprints, "keyword_owners", lambda *args, **kwargs: [])
    monkeypatch.setattr(blueprints, "duplicate_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(blueprints, "structural_duplicate_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(approval, "keyword_owners", lambda *args, **kwargs: [])
    monkeypatch.setattr(quality, "duplicate_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr(quality, "structural_duplicate_candidates", lambda *args, **kwargs: [])

    manifest = _load(BATCH / "manifest.json")
    assert manifest["publication_policy"] == "draft_only_no_schedule_no_publish"
    assert len(manifest["articles"]) == 5

    fingerprints = set()
    source_refs = set()
    approved_packages = []

    for spec in manifest["articles"]:
        plan = _matching_plan(spec)
        blueprint = blueprint_from_plan(plan)
        assert blueprint["article_id"] == spec["article_id"]
        assert blueprint["status"] == "ready_for_draft", blueprint.get("duplicate_hits")
        assert blueprint["subject_lottery"] == "分分彩"
        assert blueprint["subject_play"] == spec["subject_play"]
        assert blueprint["resolved_selector"] == spec["resolved_selector"]
        assert blueprint["source_support_count"] == spec["source_support_count"]

        packet = build_draft_packet(blueprint)
        assert packet["immutable_facts"]["source_refs"] == plan["source_refs"]
        assert packet["case_bundle"]["selector"] == spec["resolved_selector"]
        assert packet["case_bundle"]["must_label_as"] == "演示数据，不是真实开奖记录"

        article = _load(BATCH / "articles" / f"{spec['article_id']}.json")
        assert article["primary_keyword"] == packet["seo"]["primary_keyword"]
        assert article["search_intent"] == packet["seo"]["search_intent"]
        assert article["rule_refs"] == packet["immutable_facts"]["rule_refs"]
        assert article["site_category_key"] == "tzjq"
        assert article["content_format"] == "html"
        assert "演示数据，不是真实开奖记录" in article["content"]

        # Title SEO V1.0: inject title_candidates so apply_title_seo uses
        # the original title instead of regenerating one that may fail gates.
        play = spec.get("subject_play") or packet.get("immutable_facts", {}).get("play") or ""
        if "title_candidates" not in article:
            article["title_seo_contract_version"] = TITLE_SEO_CONTRACT_VERSION
            article["title_selection_reason"] = "smoke batch2 regression"
            original_title = str(article.get("title") or "")
            generated = suggest_title_candidates(article, 4)
            article["title_candidates"] = list(dict.fromkeys([original_title, *generated]))[:5]
            # Update search_intent to contain play-specific domain terms
            enriched_intent = f"学习{play}的复算案例和筛选步骤"
            article["search_intent"] = enriched_intent
            packet["seo"]["search_intent"] = enriched_intent

        result = evaluate_for_approval(packet, article)
        assert result.approved, f"{spec['article_id']}: {result.errors}"
        assert result.quality_score >= 80
        package = result.publish_package
        assert package is not None
        assert package["status"] == "approved"
        assert package["subject_lottery"] == "分分彩"
        assert package["subject_play"] == spec["subject_play"]
        assert package["site_category_key"] == "tzjq"
        assert package["content_format"] == "html"
        assert spec["source_ref"] in package["source_refs"]
        assert "publish_at" not in package

        expected = _load(BATCH / "approved" / f"{spec['article_id']}.json")
        assert expected["approved_at"] == "2026-08-11T12:45:00+00:00"
        assert package["content_hash"] == expected["content_hash"]
        actual_cmp = dict(package)
        expected_cmp = dict(expected)
        actual_cmp.pop("approved_at", None)
        expected_cmp.pop("approved_at", None)
        # Title SEO V1.0 may rewrite title/seo_title and adds new contract fields.
        for title_field in ("title", "seo_title", "title_seo_contract_version",
                            "title_candidates", "title_selection_reason", "title_review"):
            actual_cmp.pop(title_field, None)
            expected_cmp.pop(title_field, None)
        assert actual_cmp == expected_cmp, f"{spec['article_id']}: frozen Approved Package drifted"

        fingerprints.add(package["fingerprint"])
        source_refs.add(spec["source_ref"])
        approved_packages.append(package)

    assert len(fingerprints) == 5
    assert len(source_refs) == 5
    assert len(approved_packages) == 5


def test_batch2_articles_do_not_embed_unverified_provider_economics():
    manifest = _load(BATCH / "manifest.json")
    forbidden = ("返点", "赔率", "稳赚", "必中", "包赢", "必赚")
    for spec in manifest["articles"]:
        article = _load(BATCH / "articles" / f"{spec['article_id']}.json")
        content = article["content"]
        for term in forbidden:
            assert term not in content, f"{spec['article_id']} contains blocked term: {term}"
