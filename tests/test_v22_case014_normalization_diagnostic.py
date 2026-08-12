from __future__ import annotations

from engine.ai_generation_v22 import _claim_matches_pipeline_result, _normalize_multistage_article
from engine.draft_pipeline_v22 import build_multistage_draft_packet
from engine.stability_suite_20_v22 import stability_suite_20


def _packet() -> dict:
    for blueprint, _ in stability_suite_20():
        if blueprint["article_id"] == "LCM-STAB20-V22-014":
            return build_multistage_draft_packet(blueprint)
    raise AssertionError("case 014 missing")


def test_exact_real_case014_first_row_is_matchable_and_normalized():
    packet = _packet()
    claim = "从 1000 个有序三位数组合开始，先按‘恰好1个奇数’筛到 375 个，排除 625 个。"
    assert packet["immutable_facts"]["rule_refs"] == ["SSC-HIST-MECH-3STAR-LAST-V1"]
    assert _claim_matches_pipeline_result(packet, claim)

    article = {
        "content": "<p>演示数据，不是真实开奖记录。</p>",
        "claim_evidence": [
            {
                "claim_text": claim,
                "claim_type": "calculation",
                "support_type": "verified_rule",
                "support_refs": [],
                "evidence_note": "第一层机器冻结结果。",
            }
        ],
    }
    normalized = _normalize_multistage_article(article, packet)
    first = normalized["claim_evidence"][0]
    assert first["support_refs"] == ["SSC-HIST-MECH-3STAR-LAST-V1"]
    assert "system-normalized" in first["evidence_note"]
