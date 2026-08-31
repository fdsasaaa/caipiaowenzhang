import json
from collections import Counter
from pathlib import Path

from engine.ai_generation import validate_generated_identity
from engine.approval import evaluate_for_approval
from engine.claim_evidence import audit_claim_evidence
from engine.draft_packets import build_draft_packet
from engine.title_seo import TITLE_SEO_CONTRACT_VERSION
from engine.title_seo_runtime import suggest_title_candidates

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "agent" / "results" / "v2-quality-smoke-001"


def _load(name: str) -> dict:
    return json.loads((CASE_DIR / name).read_text(encoding="utf-8"))


def test_v2_quality_smoke_article_passes_full_approval_pipeline():
    blueprint = _load("blueprint.json")
    article = _load("article.json")
    packet = build_draft_packet(blueprint)

    assert packet["editorial_contract_version"] == "1.0"
    assert packet["practicality"]["must_state_stop_condition"] is True

    # Prove the worked example is exactly the deterministic V2 Draft Packet case.
    assert packet["case_bundle"]["draws"][-12:] == [
        "76738", "57809", "70691", "45410", "70624", "28126",
        "47947", "12259", "13805", "38327", "76454", "69408",
    ]
    assert packet["case_bundle"]["descriptive"]["sum_series"] == [
        18, 17, 16, 5, 12, 9, 20, 16, 13, 12, 13, 12,
    ]
    inside = [x for x in packet["case_bundle"]["descriptive"]["sum_series"] if 10 <= x <= 17]
    assert len(inside) == 8

    # Independently recompute the theoretical ordered outcome-space coverage.
    sum_counts = Counter(a + b + c for a in range(10) for b in range(10) for c in range(10))
    assert [sum_counts[s] for s in range(10, 18)] == [63, 69, 73, 75, 75, 73, 69, 63]
    assert sum(sum_counts[s] for s in range(10, 18)) == 560
    assert 1000 - 560 == 440

    # Same immutable identity contract used after a real Responses API call.
    validate_generated_identity(packet, article)

    evidence = audit_claim_evidence(packet, article)
    assert evidence.passed, evidence.errors

    # Title SEO V1.0: the frozen article has a generic search_intent that
    # predates the title SEO contract. Inject play-specific intent and candidates
    # so apply_title_seo selects the original title without rewriting it.
    play = packet.get("immutable_facts", {}).get("play") or packet.get("immutable_facts", {}).get("subject_play") or "后三直选"
    enriched_intent = f"学习{play}和值筛选的复算案例和候选空间变化"
    article["search_intent"] = enriched_intent
    packet["seo"]["search_intent"] = enriched_intent
    article["title_seo_contract_version"] = TITLE_SEO_CONTRACT_VERSION
    article["title_selection_reason"] = "smoke regression: frozen fixture compatibility"
    original_title = str(article.get("title") or "")
    generated = suggest_title_candidates(article, 4)
    article["title_candidates"] = list(dict.fromkeys([original_title, *generated]))[:5]

    result = evaluate_for_approval(packet, article)
    assert result.approved, result.errors
    assert result.status == "approved"
    assert result.quality_score == 100
    assert result.editorial_score == 100
    assert result.errors == []
    assert result.publish_package is not None
    assert result.publish_package["article_id"] == article["article_id"]
    assert result.publish_package["content"] == article["content"]
    assert result.publish_package["editorial_contract_version"] == "1.0"
    assert result.publish_package["practical_guidance"]["after_primary_filter_space"].startswith("560")
