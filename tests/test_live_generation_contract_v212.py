from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from engine.ai_generation import build_generation_prompt
from engine.claim_evidence import audit_claim_evidence
from engine.draft_packets import build_draft_packet, review_draft

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "agent" / "results" / "v2-quality-smoke-001" / "blueprint.json"
ARTICLE = ROOT / "agent" / "results" / "v2-quality-smoke-001" / "article.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_primary_filter_contract_is_explicit_in_draft_packet_and_prompt():
    packet = build_draft_packet(_load(BLUEPRINT))
    spec = packet["practicality"]["primary_filter_spec"]

    assert spec["metric"] == "digit_sum"
    assert spec["selector"] == "后三"
    assert spec["min"] == 10
    assert spec["max"] == 17
    assert spec["starting_space"] == 1000
    assert spec["after_filter_space"] == 560
    assert spec["excluded_space"] == 440
    assert spec["basis"] == "source_unverified_hypothesis"
    assert packet["case_bundle"]["primary_filter_spec"] == spec

    prompt = build_generation_prompt(packet)
    assert 'support_refs 必须严格等于 ["case_bundle"]' in prompt
    assert "绝不能把 case_bundle.sample_size 或演示样本条数当成理论候选空间" in prompt
    assert "title 与 seo_title 应自然包含 exact primary_keyword" in prompt
    assert "starting_space" in prompt and "after_filter_space" in prompt and "excluded_space" in prompt


def test_mechanics_only_economics_disclaimer_is_not_misclassified_as_fact():
    packet = build_draft_packet(_load(BLUEPRINT))
    article = deepcopy(_load(ARTICLE))
    article["content"] = (
        "<p>本文不讨论未核验的赔率、返点、奖金或收益。</p>" + article["content"]
    )

    review = review_draft(packet, article)
    assert review.passed, review.errors
    assert not any("factual 赔率 statement" in error for error in review.errors)
    assert not any("factual 返点 statement" in error for error in review.errors)


def test_synthetic_case_negation_uses_only_case_bundle_and_wrong_ref_still_fails():
    packet = build_draft_packet(_load(BLUEPRINT))
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>演示数据，不是真实开奖记录。</p>",
        "claim_evidence": [
            {
                "claim_text": "演示数据，不是真实开奖记录。",
                "claim_type": "editorial",
                "support_type": "synthetic_case",
                "support_refs": ["case_bundle"],
                "evidence_note": "明确标记案例来源为Draft Packet演示数据。",
            }
        ],
    }

    report = audit_claim_evidence(packet, article)
    assert report.passed, report.errors

    bad = deepcopy(article)
    bad["claim_evidence"][0]["support_refs"] = [packet["immutable_facts"]["source_refs"][0]]
    bad_report = audit_claim_evidence(packet, bad)
    assert not bad_report.passed
    assert any("synthetic_case must reference only case_bundle" in error for error in bad_report.errors)


def test_synthetic_case_numeric_fact_must_still_use_case_bundle():
    packet = build_draft_packet(_load(BLUEPRINT))
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>演示样本共有12条，最后一条是69408。</p>",
        "claim_evidence": [
            {
                "claim_text": "演示样本共有12条，最后一条是69408。",
                "claim_type": "calculation",
                "support_type": "synthetic_case",
                "support_refs": ["case_bundle"],
                "evidence_note": "由case_bundle直接读取并复算。",
            }
        ],
    }
    report = audit_claim_evidence(packet, article)
    assert report.passed, report.errors
