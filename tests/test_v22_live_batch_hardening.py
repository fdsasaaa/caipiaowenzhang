from __future__ import annotations

import json
from pathlib import Path

from engine.ai_generation_v22 import _normalize_multistage_article
from engine.claim_evidence import audit_claim_evidence
from engine.draft_pipeline_v22 import build_multistage_draft_packet

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "agent" / "benchmarks" / "v22-live-batch"


def _packet() -> dict:
    return {
        "immutable_facts": {
            "rule_refs": ["SSC-HIST-MECH-2STAR-GROUP-V1"],
            "source_refs": [],
            "case_scope": "mechanics_only",
        }
    }


def test_negative_performance_language_is_not_misclassified_as_positive_claim():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>这个数字是确定性空间计算，不是命中率，也不是优势判断。</p>",
        "claim_evidence": [],
    }
    report = audit_claim_evidence(_packet(), article)
    assert report.passed, report.errors


def test_actual_positive_hit_rate_still_requires_evidence():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>这个方法的命中率为60%。</p>",
        "claim_evidence": [],
    }
    report = audit_claim_evidence(_packet(), article)
    assert not report.passed
    assert any("hard claim sentence lacks claim_evidence" in error for error in report.errors)


def test_repeated_bet_count_sentence_can_reuse_same_exact_quantitative_evidence():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>按这个条件复算，空间从45注变成10注，排除35注。</p>",
        "claim_evidence": [
            {
                "claim_text": "第一层把后二组选理论空间从45注缩到10注，排除35注。",
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": ["SSC-HIST-MECH-2STAR-GROUP-V1"],
                "evidence_note": "由固定候选池枚举复算。",
            }
        ],
    }
    report = audit_claim_evidence(_packet(), article)
    assert report.passed, report.errors


def test_different_bet_count_cannot_borrow_unrelated_quantitative_evidence():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>按这个条件复算，最后剩8注。</p>",
        "claim_evidence": [
            {
                "claim_text": "第一层把后二组选理论空间从45注缩到10注，排除35注。",
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": ["SSC-HIST-MECH-2STAR-GROUP-V1"],
                "evidence_note": "由固定候选池枚举复算。",
            }
        ],
    }
    report = audit_claim_evidence(_packet(), article)
    assert not report.passed


def test_v22_normalizes_editorial_placeholder_refs_to_empty_array():
    article = {
        "claim_evidence": [
            {
                "claim_text": "本文只讲机械复算。",
                "claim_type": "editorial",
                "support_type": "editorial",
                "support_refs": ["rule_refs"],
                "evidence_note": "边界说明。",
            }
        ]
    }
    normalized = _normalize_multistage_article(article)
    assert normalized["claim_evidence"][0]["support_refs"] == []
    assert article["claim_evidence"][0]["support_refs"] == ["rule_refs"]


def test_v22_uses_semantic_synthetic_case_label_gate():
    blueprint = json.loads((BENCH / "004-blueprint.json").read_text(encoding="utf-8"))
    packet = build_multistage_draft_packet(blueprint)
    assert packet["output_contract"]["must_include_case_label"] == "不是真实开奖记录"
