from __future__ import annotations

from engine.ai_generation_v22 import _normalize_multistage_article
from engine.claim_evidence import audit_claim_evidence
from engine.draft_pipeline_v22 import build_multistage_draft_packet
from engine.stability_suite_v22 import stability_suite


def _case003_packet() -> dict:
    blueprint, _ = stability_suite()[2]
    assert blueprint["article_id"] == "LCM-STAB-V22-003"
    return build_multistage_draft_packet(blueprint)


def _placeholder_row(text: str) -> dict:
    return {
        "claim_text": text,
        "claim_type": "calculation",
        "support_type": "verified_rule",
        "support_refs": ["rule_refs"],
        "evidence_note": "模型把提示词里的字段名误当成了实际ref。",
    }


def test_pipeline_calculation_placeholder_rule_refs_are_normalized_to_packet_rules():
    packet = _case003_packet()
    article = {
        "generation_contract_version": "2.0",
        "content": (
            "<p>演示数据，不是真实开奖记录。</p>"
            "<p>第1层恰好1个大号：1000 -> 375，排除625。</p>"
            "<p>第2层三位全异：375 -> 300，排除75。</p>"
            "<p>整体：1000 -> 300，总排除700。</p>"
        ),
        "claim_evidence": [
            _placeholder_row("第1层恰好1个大号：1000 -> 375，排除625。"),
            _placeholder_row("第2层三位全异：375 -> 300，排除75。"),
            _placeholder_row("整体：1000 -> 300，总排除700。"),
        ],
    }
    normalized = _normalize_multistage_article(article, packet)
    expected = ["SSC-DERIVED-MECH-MIDDLE3-DIRECT-V1"]
    for row in normalized["claim_evidence"][:3]:
        assert row["support_type"] == "verified_rule"
        assert row["support_refs"] == expected
        assert "system-normalized" in row["evidence_note"]
    report = audit_claim_evidence(packet, normalized)
    assert report.passed, report.errors


def test_non_pipeline_placeholder_rule_ref_is_not_silently_normalized():
    packet = _case003_packet()
    article = {
        "generation_contract_version": "2.0",
        "content": "<p>某个额外规则事实。</p>",
        "claim_evidence": [
            {
                "claim_text": "某个额外规则事实。",
                "claim_type": "rule_fact",
                "support_type": "verified_rule",
                "support_refs": ["rule_refs"],
                "evidence_note": "这不是机器pipeline数学。",
            }
        ],
    }
    normalized = _normalize_multistage_article(article, packet)
    assert normalized["claim_evidence"][0]["support_refs"] == ["rule_refs"]
    report = audit_claim_evidence(packet, normalized)
    assert not report.passed
    assert any("references rule outside Draft Packet" in error for error in report.errors)
