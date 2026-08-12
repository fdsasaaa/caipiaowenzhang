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


def _calc(claim_text: str) -> dict:
    return {
        "claim_text": claim_text,
        "claim_type": "calculation",
        "support_type": "verified_rule",
        "support_refs": ["SSC-HIST-MECH-2STAR-GROUP-V1"],
        "evidence_note": "由预冻结筛选合同确定性复算。",
    }


def test_negative_performance_language_is_not_misclassified_as_positive_claim():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>这个数字是确定性空间计算，不是命中率，也不是优势判断。</p>",
        "claim_evidence": [],
    }
    report = audit_claim_evidence(_packet(), article)
    assert report.passed, report.errors


def test_natural_negative_hit_rate_phrase_from_live_batch_is_not_positive_claim():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>这个变化只是在候选空间里做确定性分组，不是在说命中率更高。</p>",
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


def test_positive_relative_hit_rate_still_requires_evidence():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>这个结构的命中率更高。</p>",
        "claim_evidence": [],
    }
    report = audit_claim_evidence(_packet(), article)
    assert not report.passed


def test_repeated_bet_count_sentence_can_reuse_same_exact_quantitative_evidence():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>按这个条件复算，空间从45注变成10注，排除35注。</p>",
        "claim_evidence": [_calc("第一层把后二组选理论空间从45注缩到10注，排除35注。")],
    }
    report = audit_claim_evidence(_packet(), article)
    assert report.passed, report.errors


def test_bare_pool_digits_do_not_poison_bet_count_evidence_matching():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>第一步只套用候选数字池0/2/5/7/9，逐个核算后得到10注，写清楚排除了35注。</p>",
        "claim_evidence": [_calc("第一层把45注压到10注，排除35注。")],
    }
    report = audit_claim_evidence(_packet(), article)
    assert report.passed, report.errors


def test_one_sentence_can_use_union_of_multiple_verified_quantity_rows():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>这个案例已经把预冻结的两层都跑完了：45注到10注，再到7注。</p>",
        "claim_evidence": [
            _calc("第一层把45注压到10注，排除35注。"),
            _calc("第二层把10注压到7注，排除3注。"),
        ],
    }
    report = audit_claim_evidence(_packet(), article)
    assert report.passed, report.errors


def test_different_bet_count_cannot_borrow_unrelated_quantitative_evidence():
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>按这个条件复算，最后剩8注。</p>",
        "claim_evidence": [_calc("第一层把后二组选理论空间从45注缩到10注，排除35注。")],
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


def test_v22_deterministically_injects_missing_synthetic_disclosure():
    blueprint = json.loads((BENCH / "004-blueprint.json").read_text(encoding="utf-8"))
    packet = build_multistage_draft_packet(blueprint)
    article = {
        "content": "<p>下面使用演示样本说明步骤。</p>",
        "claim_evidence": [],
    }
    normalized = _normalize_multistage_article(article, packet)
    assert normalized["content"].startswith("<p><strong>演示数据，不是真实开奖记录。</strong></p>")
    assert normalized["claim_evidence"][-1]["support_type"] == "synthetic_case"
    assert normalized["claim_evidence"][-1]["support_refs"] == ["case_bundle"]


def test_v22_does_not_duplicate_existing_synthetic_disclosure():
    blueprint = json.loads((BENCH / "004-blueprint.json").read_text(encoding="utf-8"))
    packet = build_multistage_draft_packet(blueprint)
    content = "<p>演示数据，不是真实开奖记录。</p><p>继续复算。</p>"
    article = {"content": content, "claim_evidence": []}
    normalized = _normalize_multistage_article(article, packet)
    assert normalized["content"] == content
    assert normalized["claim_evidence"] == []
