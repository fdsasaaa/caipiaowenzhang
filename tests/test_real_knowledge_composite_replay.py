from __future__ import annotations

import json
from pathlib import Path

from engine.ai_generation import build_generation_prompt
from engine.approval import evaluate_for_approval
from engine.batch_quality_v22 import evaluate_multistage
from engine.real_knowledge_composite_article_contract import (
    build_composite_article_packet,
    evaluate_composite_article_content,
)
from engine.real_knowledge_composite_evidence import normalize_composite_claim_metadata


FIXTURE = Path(__file__).parent / "fixtures" / "real_knowledge_composite_live_2026_08_12.json"


def _load_article() -> tuple[str, dict]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return payload["response_id"], payload["article"]


def test_same_live_response_replays_to_full_acceptance_without_rewriting_content():
    response_id, article = _load_article()
    packet = build_composite_article_packet()
    original_content = article["content"]

    replayed = normalize_composite_claim_metadata(packet, article)
    approval = evaluate_for_approval(packet, replayed)
    multistage = evaluate_multistage(packet, replayed)
    composite = evaluate_composite_article_content(replayed)

    assert response_id == "resp_0387a28a45beb483016a7c8fb4fc088199a786f0aba5f7d202"
    assert replayed["content"] == original_content
    assert approval.approved is True, approval.errors
    assert approval.quality_score == 100
    assert approval.editorial_score == 100
    assert multistage.passed is True, multistage.errors
    assert multistage.score == 100
    assert composite.passed is True, composite.errors
    assert composite.score == 100


def test_ffc_generation_prompt_encodes_reader_facing_term_preference_without_mutating_provenance():
    packet = build_composite_article_packet()
    prompt = build_generation_prompt(packet)

    assert "面向读者的彩种显示名统一优先使用‘分分彩’" in prompt
    assert "来源原文里出现‘时时彩’" in prompt
    assert "内部 mechanics/provenance 层保持真实原始术语" in prompt
    assert packet["immutable_facts"]["source_refs"] == ["BRBCW-006020", "BRBCW-002590"]
    assert packet["immutable_facts"]["rule_refs"] == ["SSC-HIST-MECH-3STAR-LAST-V1"]
