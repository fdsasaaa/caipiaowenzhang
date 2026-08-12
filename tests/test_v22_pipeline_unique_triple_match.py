from __future__ import annotations

from copy import deepcopy

from engine.ai_generation_v22 import _claim_matches_pipeline_result, _normalize_multistage_article
from engine.draft_pipeline_v22 import build_multistage_draft_packet
from engine.stability_suite_20_v22 import stability_suite_20


def _packet(case_id: str) -> dict:
    for blueprint, _ in stability_suite_20():
        if blueprint["article_id"].endswith("-" + case_id):
            return build_multistage_draft_packet(blueprint)
    raise AssertionError(case_id)


def test_unique_stage_triple_matches_natural_prose_without_exact_label_format():
    packet = _packet("014")
    claim = "从1000个有序候选开始，先按条件筛到375个，并排除625个。"
    assert _claim_matches_pipeline_result(packet, claim)


def test_partial_stage_numbers_do_not_match_pipeline():
    packet = _packet("014")
    claim = "从1000个候选开始筛到375个。"
    assert not _claim_matches_pipeline_result(packet, claim)


def test_unique_triple_requires_calculation_language():
    packet = _packet("014")
    claim = "资料编号1000、375、625。"
    assert not _claim_matches_pipeline_result(packet, claim)


def test_ambiguous_duplicate_stage_triple_does_not_auto_normalize():
    packet = _packet("014")
    changed = deepcopy(packet)
    first = changed["practicality"]["filter_pipeline_result"]["stages"][0]
    duplicate = deepcopy(first)
    duplicate["index"] = 99
    duplicate["id"] = "duplicate_test_stage"
    changed["practicality"]["filter_pipeline_result"]["stages"].append(duplicate)

    claim = "从1000个候选开始筛到375个，排除625个。"
    assert not _claim_matches_pipeline_result(changed, claim)

    article = {
        "content": "<p>演示数据，不是真实开奖记录。</p>",
        "claim_evidence": [
            {
                "claim_text": claim,
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": [],
                "evidence_note": "ambiguous triple must stay invalid",
            }
        ],
    }
    normalized = _normalize_multistage_article(article, changed)
    assert normalized["claim_evidence"][0]["support_refs"] == []
