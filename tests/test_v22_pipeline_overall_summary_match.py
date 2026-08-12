from __future__ import annotations

from engine.ai_generation_v22 import _claim_matches_pipeline_result, _normalize_multistage_article
from engine.draft_pipeline_v22 import build_multistage_draft_packet
from engine.stability_suite_20_v22 import stability_suite_20


def _packet() -> dict:
    for blueprint, _ in stability_suite_20():
        if blueprint["article_id"] == "LCM-STAB20-V22-014":
            return build_multistage_draft_packet(blueprint)
    raise AssertionError("case 014 missing")


def test_overall_summary_can_omit_repeated_starting_count():
    packet = _packet()
    claim = "三层全部完成后，最终候选空间是141个，总共排除859个。"
    assert _claim_matches_pipeline_result(packet, claim)

    article = {
        "content": "<p>演示数据，不是真实开奖记录。</p>",
        "claim_evidence": [
            {
                "claim_text": claim,
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": [],
                "evidence_note": "整体机器冻结结果。",
            }
        ],
    }
    normalized = _normalize_multistage_article(article, packet)
    assert normalized["claim_evidence"][0]["support_refs"] == ["SSC-HIST-MECH-3STAR-LAST-V1"]


def test_two_overall_numbers_without_overall_semantics_do_not_match():
    packet = _packet()
    assert not _claim_matches_pipeline_result(packet, "资料编号141和859。")


def test_only_final_space_is_not_enough_for_overall_match():
    packet = _packet()
    assert not _claim_matches_pipeline_result(packet, "三层完成后最终候选空间是141个。")
