from __future__ import annotations

from engine.ai_generation_v22 import _normalize_multistage_article
from engine.claim_evidence import audit_claim_evidence
from engine.draft_packets import _contains_factual_economics_statement
from engine.draft_pipeline_v22 import build_multistage_draft_packet
from engine.stability_suite_20_v22 import stability_suite_20


def _packet(case_id: str) -> dict:
    for blueprint, _ in stability_suite_20():
        if blueprint["article_id"].endswith("-" + case_id):
            return build_multistage_draft_packet(blueprint)
    raise AssertionError(case_id)


def _minimal_packet() -> dict:
    return {
        "immutable_facts": {
            "rule_refs": ["SSC-HIST-MECH-3STAR-LAST-V1"],
            "source_refs": [],
            "case_scope": "mechanics_only",
        }
    }


def _article(sentence: str) -> dict:
    return {
        "generation_contract_version": "2.0",
        "content": f"<p>{sentence}</p>",
        "claim_evidence": [],
    }


def test_real_negative_safety_phrases_from_stability_20_are_not_positive_claims():
    sentences = [
        "这一层只是在总空间里保留符合数字池的组合，不要把它理解成命中率、胜率或任何收益结论。",
        "这里的 before、after、excluded 都要按同一口径记录，不能把它写成收益、命中率或者胜率。",
        "它们能用来复算候选空间，但不能被写成历史优势、命中率优势或收益优势。",
        "这里仍然只是确定性筛选，不能把这个结果解释成收益、胜率或未来表现。",
        "这里仍然只是把参数固定后逐层复算，不能把结果写成收益、命中率或胜率。",
    ]
    for sentence in sentences:
        report = audit_claim_evidence(_minimal_packet(), _article(sentence))
        assert report.passed, (sentence, report.errors)


def test_real_negative_odds_phrase_is_not_factual_provider_economics():
    sentence = "这个结果还是空间计算，不是收益、赔率或胜率。"
    assert not _contains_factual_economics_statement(sentence, "赔率")


def test_positive_or_numeric_economics_still_fail_provider_gate():
    assert _contains_factual_economics_statement("这个平台赔率为2000。", "赔率")
    assert _contains_factual_economics_statement("这不是收益，但实际赔率更高。", "赔率")
    assert _contains_factual_economics_statement("不能把赔率2000当成通用参数。", "赔率")
    assert not _contains_factual_economics_statement("本文不讨论未核验的平台赔率。", "赔率")


def test_positive_or_numeric_performance_statements_still_need_evidence():
    for sentence in (
        "这个结构的胜率更高。",
        "这组参数的命中率为60%。",
        "不能证明胜率，但实际胜率更高。",
        "不用于证明胜率60%。",
    ):
        report = audit_claim_evidence(_minimal_packet(), _article(sentence))
        assert not report.passed, sentence


def test_case014_exact_pipeline_verified_rule_rows_with_empty_refs_are_repaired():
    packet = _packet("014")
    article = {
        "claim_evidence": [
            {
                "claim_text": "从 1000 个有序三位数组合开始，先按‘恰好1个奇数’筛到 375 个，排除 625 个。",
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": [],
                "evidence_note": "第一层机器冻结结果。",
            },
            {
                "claim_text": "再按‘跨度2–6’从 375 个继续筛到 234 个，排除 141 个。",
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": [],
                "evidence_note": "第二层机器冻结结果。",
            },
            {
                "claim_text": "最后按‘和值8–18’从 234 个继续筛到 141 个，排除 93 个。",
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": [],
                "evidence_note": "第三层机器冻结结果。",
            },
            {
                "claim_text": "三层全部完成后，最终候选空间是 141 个，总共排除 859 个。",
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": [],
                "evidence_note": "整体机器冻结结果。",
            },
        ],
        "content": "<p>演示数据，不是真实开奖记录。</p>",
    }
    normalized = _normalize_multistage_article(article, packet)
    expected = ["SSC-HIST-MECH-3STAR-LAST-V1"]
    for row in normalized["claim_evidence"][:4]:
        assert row["support_refs"] == expected
        assert "system-normalized" in row["evidence_note"]


def test_case020_exact_pipeline_empty_refs_are_repaired():
    packet = _packet("020")
    article = {
        "claim_evidence": [
            {
                "claim_text": "第1层 候选数字池1/2/4/5/6/8: 1000 -> 216，排除 784；basis=experimental_parameter",
                "claim_type": "calculation", "support_type": "verified_rule", "support_refs": [], "evidence_note": "stage1",
            },
            {
                "claim_text": "第2层 恰好2个大号: 216 -> 81，排除 135；basis=experimental_parameter",
                "claim_type": "calculation", "support_type": "verified_rule", "support_refs": [], "evidence_note": "stage2",
            },
            {
                "claim_text": "整体：1000 -> 81，总排除 919。",
                "claim_type": "calculation", "support_type": "verified_rule", "support_refs": [], "evidence_note": "overall",
            },
        ],
        "content": "<p>演示数据，不是真实开奖记录。</p>",
    }
    normalized = _normalize_multistage_article(article, packet)
    expected = ["SSC-DERIVED-MECH-MIDDLE3-DIRECT-V1"]
    for row in normalized["claim_evidence"][:3]:
        assert row["support_refs"] == expected


def test_non_pipeline_verified_rule_with_empty_refs_remains_invalid():
    packet = _packet("020")
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>某个额外规则事实。</p>",
        "claim_evidence": [
            {
                "claim_text": "某个额外规则事实。",
                "claim_type": "rule_fact",
                "support_type": "verified_rule",
                "support_refs": [],
                "evidence_note": "不是机器pipeline。",
            }
        ],
    }
    normalized = _normalize_multistage_article(article, packet)
    assert normalized["claim_evidence"][0]["support_refs"] == []
    report = audit_claim_evidence(packet, normalized)
    assert not report.passed
    assert any("verified_rule requires support_refs" in error for error in report.errors)
