from __future__ import annotations

from engine.claim_evidence import audit_claim_evidence
from engine.real_group6_article_contract import build_real_group6_article_packet

POLICY_REF = "USER-BET-COMPLIANCE-90-V1"
POLICY_SENTENCE = (
    "720/1000=72%只表示组六结构占全部三位有序结果的比例，不是本项目的可执行投注覆盖率；"
    "若把120个单位全部使用，对组六目标域覆盖率是100%，超过90%上限，因此本文不得把“全120单位”写成可执行投注方案"
)


def _article(entry: dict) -> dict:
    return {
        "generation_contract_version": "2.0",
        "content": f"<p>{POLICY_SENTENCE}。</p>",
        "claim_evidence": [entry],
    }


def test_policy_contract_can_support_exact_internal_coverage_guardrail_sentence():
    packet = build_real_group6_article_packet()
    article = _article({
        "claim_text": POLICY_SENTENCE,
        "claim_type": "calculation",
        "support_type": "policy_contract",
        "support_refs": [POLICY_REF],
        "evidence_note": "90%来自用户定义的内部投注合规政策，不是平台玩法事实。",
    })
    report = audit_claim_evidence(packet, article)
    assert report.passed is True, report.errors


def test_policy_contract_cannot_reference_unknown_policy():
    packet = build_real_group6_article_packet()
    article = _article({
        "claim_text": POLICY_SENTENCE,
        "claim_type": "calculation",
        "support_type": "policy_contract",
        "support_refs": ["OTHER-POLICY"],
        "evidence_note": "wrong ref",
    })
    report = audit_claim_evidence(packet, article)
    assert report.passed is False
    assert any("must reference only" in error for error in report.errors)


def test_policy_contract_cannot_prove_performance_claim():
    packet = build_real_group6_article_packet()
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>命中率更高。</p>",
        "claim_evidence": [{
            "claim_text": "命中率更高",
            "claim_type": "performance",
            "support_type": "policy_contract",
            "support_refs": [POLICY_REF],
            "evidence_note": "policy cannot prove performance",
        }],
    }
    report = audit_claim_evidence(packet, article)
    assert report.passed is False
    assert any("cannot prove performance" in error for error in report.errors)


def test_policy_contract_is_unavailable_without_packet_policy_ref():
    packet = build_real_group6_article_packet()
    packet = dict(packet)
    packet["compliance"] = {}
    article = _article({
        "claim_text": POLICY_SENTENCE,
        "claim_type": "calculation",
        "support_type": "policy_contract",
        "support_refs": [POLICY_REF],
        "evidence_note": "missing packet policy",
    })
    report = audit_claim_evidence(packet, article)
    assert report.passed is False
    assert any("without Draft Packet compliance policy" in error for error in report.errors)
