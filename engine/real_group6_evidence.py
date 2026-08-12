from __future__ import annotations

from copy import deepcopy

from .real_group6_article_contract import DOMAIN_BOUNDARY, SOURCE_BOUNDARY

POLICY_REF = "USER-BET-COMPLIANCE-90-V1"
GROUP6_RULE_REF = "SSC-HIST-MECH-3STAR-GROUP6-V1"
SOURCE_REF = "BRBCW-004115"

MECHANICS_SENTENCE, POLICY_SENTENCE = DOMAIN_BOUNDARY.split("。", 1)
MECHANICS_SENTENCE += "。"


class RealGroup6EvidenceError(ValueError):
    pass


def normalize_real_group6_claim_metadata(packet: dict, article: dict) -> dict:
    """Append canonical evidence for locked group6 boundaries without rewriting content."""
    contract = packet.get("real_group6_validation") or {}
    if not contract:
        raise RealGroup6EvidenceError("real_group6_validation contract missing")
    entries = article.get("claim_evidence")
    if not isinstance(entries, list):
        raise RealGroup6EvidenceError("claim_evidence must be a list")

    facts = packet.get("immutable_facts") or {}
    if facts.get("rule_refs") != [GROUP6_RULE_REF]:
        raise RealGroup6EvidenceError("group6 rule_ref changed")
    if facts.get("source_refs") != [SOURCE_REF]:
        raise RealGroup6EvidenceError("group6 source_ref changed")
    if (packet.get("compliance") or {}).get("policy_ref") != POLICY_REF:
        raise RealGroup6EvidenceError("group6 compliance policy_ref changed")

    normalized = deepcopy(article)
    rows = normalized["claim_evidence"]
    exact_texts = {
        SOURCE_BOUNDARY,
        "来源内容未独立验证；" + SOURCE_BOUNDARY,
        MECHANICS_SENTENCE,
        POLICY_SENTENCE,
    }
    rows[:] = [
        row for row in rows
        if not (isinstance(row, dict) and str(row.get("claim_text") or "") in exact_texts)
    ]
    rows.extend([
        {
            "claim_text": "来源内容未独立验证；" + SOURCE_BOUNDARY,
            "claim_type": "source_claim",
            "support_type": "source_unverified",
            "support_refs": [SOURCE_REF],
            "evidence_note": (
                "compact family archive只支持 broad 组选方法原子的来源归属；"
                "group6由system_research_prefrozen合同选择，不归因给来源。"
            ),
        },
        {
            "claim_text": MECHANICS_SENTENCE,
            "claim_type": "calculation",
            "support_type": "verified_rule",
            "support_refs": [GROUP6_RULE_REF],
            "evidence_note": (
                "verified group6 mechanics + deterministic enumeration support 120 unordered units, "
                "6 ordered permutations per unit, and 720 ordered group6 outcomes."
            ),
        },
        {
            "claim_text": POLICY_SENTENCE,
            "claim_type": "calculation",
            "support_type": "policy_contract",
            "support_refs": [POLICY_REF],
            "evidence_note": (
                "72% is descriptive global structure share; the <=90% executable target-domain ceiling "
                "comes from the user-defined internal compliance policy, not a platform rule."
            ),
        },
    ])
    return normalized
