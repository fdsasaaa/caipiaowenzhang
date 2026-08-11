from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from engine.ai_generation import build_generation_prompt
from engine.claim_evidence import audit_claim_evidence
from engine.draft_packets import build_draft_packet, review_draft
from engine.editorial_quality import evaluate_editorial

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


def test_natural_source_article_qualifier_is_accepted_but_still_bound_to_source_ref():
    packet = build_draft_packet(_load(BLUEPRINT))
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>来源文章提到后三和值10–17可作为重点观察区间；该效果未独立验证，只能作为研究假设。</p>",
        "claim_evidence": [
            {
                "claim_text": "来源文章提到后三和值10–17可作为重点观察区间；该效果未独立验证，只能作为研究假设。",
                "claim_type": "source_claim",
                "support_type": "source_unverified",
                "support_refs": ["BRBCW-003412"],
                "evidence_note": "自然语言来源限定仍必须绑定Draft Packet里的来源。",
            }
        ],
    }
    report = audit_claim_evidence(packet, article)
    assert report.passed, report.errors


def test_editorial_reference_is_non_evidentiary_not_a_hard_failure():
    packet = build_draft_packet(_load(BLUEPRINT))
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>本文只讨论玩法机制和可复算步骤，不讨论未核验的平台经济参数。</p>",
        "claim_evidence": [
            {
                "claim_text": "本文只讨论玩法机制和可复算步骤，不讨论未核验的平台经济参数。",
                "claim_type": "editorial",
                "support_type": "editorial",
                "support_refs": ["SSC-HIST-MECH-3STAR-LAST-V1"],
                "evidence_note": "多余的已知ref不能让editorial变成事实证据。",
            }
        ],
    }
    report = audit_claim_evidence(packet, article)
    assert report.passed, report.errors
    assert any("non-evidentiary" in warning for warning in report.warnings)


def test_editorial_scoring_prefers_structured_filter_counts_over_range_numbers():
    packet = build_draft_packet(_load(BLUEPRINT))
    article = deepcopy(_load(ARTICLE))
    article["practical_guidance"] = {
        "steps": ["固定参数", "计算1000个空间", "保留560个", "排除440个", "没有第二规则就停止"],
        "starting_space": "后三理论空间1000个，作为主筛选前的起点。",
        "after_primary_filter_space": "后三和值10–17筛选后保留560个候选，较筛选前1000个减少440个。",
        "parameter_freeze_rule": "先固定后三和值10–17再看样本。",
        "stop_condition": "没有新的已验证规则时停止。",
        "next_step_policy": "只有已验证规则或证据才允许继续。",
    }
    article["content"] = article["content"] + "<p>主筛选明确排除440个候选。</p>"
    report = evaluate_editorial(packet, article)
    assert report.passed, report.errors
    assert report.score == 100, report.warnings
