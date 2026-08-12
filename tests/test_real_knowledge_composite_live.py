from __future__ import annotations

from engine.real_knowledge_composite_article_contract import (
    CANDIDATE_INTEGRITY_BOUNDARY,
    ORDER_BOUNDARY,
    SOURCE_BOUNDARY,
    build_composite_article_packet,
)
from engine.real_knowledge_composite_evidence import normalize_composite_claim_metadata
from scripts.real_knowledge_composite_live_article_v22 import EXPECTED, build_preflight_summary


def test_live_preflight_is_exactly_locked_and_non_publishing():
    summary = build_preflight_summary()
    assert summary["ok"] is True
    assert summary["stage"] == "real-knowledge-composite-live-v22-preflight"
    for key, value in EXPECTED.items():
        assert summary[key] == value
    assert summary["paid_model_call"] is False
    assert summary["registry_write"] is False
    assert summary["website_write"] is False
    assert summary["scheduled"] is False
    assert summary["published"] is False
    assert len(summary["spot_checks"]["included"]) == 6
    assert len(summary["spot_checks"]["excluded"]) == 6


def test_composite_evidence_normalizer_never_changes_article_content():
    packet = build_composite_article_packet()
    article = {
        "content": "<p>正文保持不变</p>",
        "claim_evidence": [
            {
                "claim_text": SOURCE_BOUNDARY,
                "claim_type": "source_claim",
                "support_type": "source_unverified",
                "support_refs": ["BRBCW-006020", "BRBCW-002590"],
                "evidence_note": "model row",
            },
            {
                "claim_text": ORDER_BOUNDARY,
                "claim_type": "calculation",
                "support_type": "synthetic_case",
                "support_refs": ["BRBCW-006020"],
                "evidence_note": "model row",
            },
            {
                "claim_text": CANDIDATE_INTEGRITY_BOUNDARY,
                "claim_type": "calculation",
                "support_type": "synthetic_case",
                "support_refs": ["BRBCW-002590"],
                "evidence_note": "model row",
            },
            {
                "claim_text": "其他模型声明",
                "claim_type": "editorial",
                "support_type": "editorial",
                "support_refs": [],
                "evidence_note": "must survive",
            },
        ],
    }
    normalized = normalize_composite_claim_metadata(packet, article)
    assert normalized["content"] == article["content"]
    assert article["claim_evidence"][0]["claim_text"] == SOURCE_BOUNDARY

    rows = {row["claim_text"]: row for row in normalized["claim_evidence"]}
    source_claim = rows["来源内容未独立验证；" + SOURCE_BOUNDARY]
    assert source_claim["support_type"] == "source_unverified"
    assert source_claim["support_refs"] == ["BRBCW-006020", "BRBCW-002590"]

    order_claim = rows[ORDER_BOUNDARY]
    assert order_claim["support_type"] == "verified_rule"
    assert order_claim["support_refs"] == ["SSC-HIST-MECH-3STAR-LAST-V1"]

    integrity_claim = rows[CANDIDATE_INTEGRITY_BOUNDARY]
    assert integrity_claim["support_type"] == "verified_rule"
    assert integrity_claim["support_refs"] == ["SSC-HIST-MECH-3STAR-LAST-V1"]

    assert rows["其他模型声明"]["evidence_note"] == "must survive"


def test_normalizer_does_not_touch_near_match_source_or_calculation_claims():
    packet = build_composite_article_packet()
    article = {
        "content": "unchanged",
        "claim_evidence": [
            {
                "claim_text": SOURCE_BOUNDARY + " 来源证明组合更好。",
                "claim_type": "source_claim",
                "support_type": "source_unverified",
                "support_refs": ["BRBCW-006020"],
                "evidence_note": "unsafe near match",
            },
            {
                "claim_text": ORDER_BOUNDARY + " 所以更容易中奖。",
                "claim_type": "calculation",
                "support_type": "synthetic_case",
                "support_refs": ["BRBCW-006020"],
                "evidence_note": "unsafe near match",
            },
        ],
    }
    normalized = normalize_composite_claim_metadata(packet, article)
    assert normalized == article
