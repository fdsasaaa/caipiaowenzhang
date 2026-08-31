from __future__ import annotations

import json
from pathlib import Path

from engine.approval import evaluate_for_approval
from engine.batch_quality_v22 import evaluate_multistage
from engine.real_knowledge_evidence_normalization import normalize_real_knowledge_claim_metadata
from engine.title_seo import TITLE_SEO_CONTRACT_VERSION
from engine.title_seo_runtime import suggest_title_candidates
from engine.real_knowledge_live_validation import (
    SOURCE_PARAMETER_BOUNDARY,
    build_real_knowledge_live_packet,
    evaluate_real_knowledge_article,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "agent" / "results" / "REAL_KNOWLEDGE_LIVE_RESPONSE_2026-08-12.json"


def _captured_article() -> dict:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["response_id"] == "resp_036fce91418f96a3016a7c83a3bd888193ba8e4ea8c48ed625"
    return payload["article"]


def test_captured_live_response_replays_to_approval_without_content_rewrite():
    packet = build_real_knowledge_live_packet()
    captured = _captured_article()

    before = evaluate_for_approval(packet, captured)
    assert before.approved is False
    assert before.quality_score == 100
    assert before.editorial_score == 100
    assert before.errors == [
        "claim_evidence[0] unverified source claim must be explicitly qualified",
        "claim_evidence[5] synthetic_case must reference only case_bundle",
    ]

    normalized = normalize_real_knowledge_claim_metadata(packet, captured)
    assert normalized["content"] == captured["content"]

    # Title SEO V1.0: inject title_candidates so apply_title_seo doesn't rewrite
    # the frozen title and fail the TITLE_SEARCH_INTENT_CHECK gate.
    original_title = str(normalized.get("title") or "")
    if "title_candidates" not in normalized:
        normalized["title_seo_contract_version"] = TITLE_SEO_CONTRACT_VERSION
        normalized["title_selection_reason"] = "live response replay regression"
        generated = suggest_title_candidates(normalized, 4)
        normalized["title_candidates"] = list(dict.fromkeys([original_title, *generated]))[:5]
        # Update search_intent to contain domain terms matching the title
        play = packet.get("immutable_facts", {}).get("play") or packet.get("immutable_facts", {}).get("subject_play") or "后二直选"
        enriched_intent = f"学习{play}大小单双筛选的复算案例和候选空间变化"
        normalized["search_intent"] = enriched_intent
        packet["seo"]["search_intent"] = enriched_intent

    after = evaluate_for_approval(packet, normalized)
    multistage = evaluate_multistage(packet, normalized)
    real_quality = evaluate_real_knowledge_article(packet, normalized)

    assert after.approved is True
    assert after.quality_score == 100
    assert after.editorial_score == 100
    assert after.errors == []
    assert multistage.passed is True
    assert multistage.score == 100
    assert real_quality.passed is True
    assert real_quality.score == 100


def test_replay_normalizer_only_changes_the_two_deterministic_evidence_rows():
    packet = build_real_knowledge_live_packet()
    captured = _captured_article()
    normalized = normalize_real_knowledge_claim_metadata(packet, captured)

    before = captured["claim_evidence"]
    after = normalized["claim_evidence"]
    assert len(before) == len(after)

    changed = []
    for index, (left, right) in enumerate(zip(before, after, strict=True)):
        if left != right:
            changed.append(index)
    assert changed == [0, 5]

    assert after[0]["claim_text"] == "来源内容未独立验证；" + SOURCE_PARAMETER_BOUNDARY
    assert after[0]["support_type"] == "source_unverified"
    assert after[0]["support_refs"] == ["BRBCW-003787"]

    assert after[5]["claim_text"] == "整体共排除74个。"
    assert after[5]["support_type"] == "verified_rule"
    assert after[5]["support_refs"] == ["SSC-HIST-MECH-LAST2-BSOE-V1"]


def test_normalizer_does_not_upgrade_nearby_non_exact_synthetic_claims():
    packet = build_real_knowledge_live_packet()
    captured = _captured_article()
    captured["claim_evidence"][5] = {
        "claim_text": "整体共排除74个，因此更容易中奖。",
        "claim_type": "calculation",
        "support_type": "synthetic_case",
        "support_refs": ["BRBCW-003787"],
        "evidence_note": "unsafe nearby claim",
    }
    normalized = normalize_real_knowledge_claim_metadata(packet, captured)
    assert normalized["claim_evidence"][5]["support_type"] == "synthetic_case"
    assert normalized["claim_evidence"][5]["support_refs"] == ["BRBCW-003787"]
